# coding: utf-8
# ID Card Recognition API - 身份证识别 REST API

import os
import base64
import io
import re
from typing import Dict, Any, Tuple
from PIL import Image
from flask import Flask, request, jsonify

# 禁用代理，避免网络连接问题
os.environ['no_proxy'] = '*'
if 'HTTP_PROXY' in os.environ:
    del os.environ['HTTP_PROXY']
if 'HTTPS_PROXY' in os.environ:
    del os.environ['HTTPS_PROXY']

app = Flask(__name__)

# 初始化 OCR 模型（仅初始化一次，以提高性能）
ocr_model = None

def get_ocr_model():
    """获取或初始化 OCR 模型"""
    global ocr_model
    if ocr_model is None:
        try:
            from cnocr import CnOcr
            # 使用本地 ch_PP-OCRv3 模型，精度最高
            # 指定本地识别模型路径
            rec_model_fp = os.path.join(os.path.dirname(__file__), 'models', 'ch_PP-OCRv3_rec_infer.onnx')
            ocr_model = CnOcr(
                rec_model_name='ch_PP-OCRv3',
                rec_model_backend='onnx',
                rec_model_fp=rec_model_fp,
                det_model_name='ch_PP-OCRv3_det'
            )
        except ImportError as e:
            raise ImportError(
                f"OCR 模型加载失败: {str(e)}\n"
                "请先安装依赖: pip install -r requirements.txt"
            )
        except Exception as e:
            raise RuntimeError(
                f"OCR 模型初始化失败: {str(e)}\n"
                f"本地模型路径: {os.path.join(os.path.dirname(__file__), 'models', 'ch_PP-OCRv3_rec_infer.onnx')}\n"
                f"详细错误: {str(e)}"
            )
    return ocr_model

def extract_name_and_id(ocr_results: list) -> Dict[str, Any]:
    """
    从 OCR 识别结果中提取姓名、身份证号、住址等信息
    
    返回格式与百度身份证识别 API 兼容的结构
    
    Args:
        ocr_results: OCR 识别结果列表
        
    Returns:
        Dict 包含识别到的各个字段及其位置信息
    """
    words_result = {}
    
    # 按位置从上到下排序（y 坐标）
    sorted_results = []
    for result in ocr_results:
        if 'position' in result:
            positions = result['position']
            y_min = int(min(pos[1] for pos in positions))
            sorted_results.append((y_min, result))
        else:
            sorted_results.append((float('inf'), result))
    
    sorted_results.sort(key=lambda x: x[0])
    sorted_texts = [result for _, result in sorted_results]
    
    # 正则表达式
    id_pattern = re.compile(r'^\d{18}$')  # 18 位身份证号
    name_pattern = re.compile(r'^[\u4e00-\u9fa5]{2,4}$')  # 2-4 个汉字
    gender_pattern = re.compile(r'^[男女]$')  # 性别
    birth_pattern = re.compile(r'^\d{8}$')  # 出生日期（8位）
    ethnicity_pattern = re.compile(r'^[\u4e00-\u9fa5]{1,4}$')  # 民族
    
    def get_location(result):
        """从识别结果中提取位置信息"""
        # 不再需要返回位置信息
        return None
    
    # 提取各个字段
    id_index = -1
    name_found = False
    
    # 第一步：找身份证号（从所有文本中查找18位数字）
    for i, result in enumerate(sorted_texts):
        text = result.get('text', '').strip()
        # 尝试从文本中提取18位数字的身份证号
        match = re.search(r'\d{18}', text)
        if match:
            id_number = match.group()
            words_result['公民身份号码'] = id_number
            id_index = i
            break
    
    # 第二步：从前面的结果中找姓名、性别、民族、出生日期
    for i in range(id_index if id_index >= 0 else len(sorted_texts)):
        result = sorted_texts[i]
        text = result.get('text', '').strip()
        
        # 姓名（2-4个汉字）
        if not name_found and name_pattern.match(text):
            name_found = True
            words_result['姓名'] = text
        
        # 性别（男/女）
        elif gender_pattern.match(text) and '性别' not in words_result:
            words_result['性别'] = text
        
        # 民族（1-4个汉字）
        elif ethnicity_pattern.match(text) and len(text) <= 4 and '民族' not in words_result:
            words_result['民族'] = text
        
        # 出生日期（8位数字）
        elif birth_pattern.match(text) and '出生' not in words_result:
            words_result['出生'] = text
    
    # 第三步：提取住址（身份证号上方，较长的中文文本）
    if id_index >= 0:
        for i in range(id_index - 1, -1, -1):
            result = sorted_texts[i]
            text = result.get('text', '').strip()
            # 住址通常是较长的中文文本（不是已识别的字段，不是身份证号）
            if (len(text) > 4 and 
                text not in words_result.values() and
                not id_pattern.search(text) and  # 不包含18位数字
                not birth_pattern.match(text) and
                any(ord(c) > 0x4e00 and ord(c) < 0x9fff for c in text) and
                '住址' not in words_result):
                words_result['住址'] = text
                break
    
    # 如果没有找到住址，尝试搜找最长的中文文本
    if '住址' not in words_result:
        max_len = 0
        for result in sorted_texts:
            text = result.get('text', '').strip()
            if (text not in words_result.values() and
                not id_pattern.match(text) and 
                not birth_pattern.match(text) and
                len(text) > max_len and
                any(ord(c) > 0x4e00 and ord(c) < 0x9fff for c in text)):
                words_result['住址'] = text
                max_len = len(text)
    
    return words_result

@app.route('/api/id_card/recognize', methods=['POST'])
def recognize_id_card() -> Dict[str, Any]:
    """
    识别身份证照片中的姓名和身份证号
    
    支持两种输入方式：
    1. 上传图片文件：form-data, key='image', value=图片文件
    2. Base64 编码的图片：JSON, key='image_base64', value=base64字符串
    
    返回 JSON 格式：
    {
        "success": true/false,
        "data": {
            "name": "姓名",
            "id_number": "身份证号",
            "confidence": 0.85
        },
        "message": "识别成功" / "错误信息"
    }
    """
    try:
        img = None
        
        # 方式1：通过文件上传
        if 'image' in request.files:
            file = request.files['image']
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'data': None,
                    'message': '未选择文件'
                }), 400
            
            # 读取图片
            img = Image.open(io.BytesIO(file.read())).convert('RGB')
        
        # 方式2：通过 Base64 编码
        elif 'image_base64' in request.json or (request.is_json and request.json):
            image_base64 = request.json.get('image_base64')
            if not image_base64:
                return jsonify({
                    'success': False,
                    'data': None,
                    'message': '缺少 image_base64 参数'
                }), 400
            
            try:
                image_bytes = base64.b64decode(image_base64)
                img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            except Exception as e:
                return jsonify({
                    'success': False,
                    'data': None,
                    'message': f'Base64 图片解码失败: {str(e)}'
                }), 400
        
        else:
            return jsonify({
                'success': False,
                'data': None,
                'message': '请上传图片文件或提供 Base64 编码的图片'
            }), 400
        
        # 执行 OCR 识别
        try:
            ocr = get_ocr_model()
        except ImportError as e:
            return jsonify({
                'success': False,
                'data': None,
                'message': str(e)
            }), 500
        
        ocr_results = ocr.ocr(img)
        
        if not ocr_results:
            return jsonify({
                'success': False,
                'data': None,
                'message': '未识别到文本内容'
            }), 200
        
        # 提取姓名、身份证号、住址
        words_result = extract_name_and_id(ocr_results)
        
        # 计算平均置信度
        confidence = sum(r.get('score', 0) for r in ocr_results) / len(ocr_results) if ocr_results else 0
        
        # 验证结果（至少需要身份证号）
        if '公民身份号码' not in words_result:
            return jsonify({
                'success': False,
                'words_result': words_result,
                'words_result_num': len(words_result),
                'image_status': 'normal',
                'message': '识别失败，未找到身份证号'
            }), 200
        
        return jsonify({
            'success': True,
            'words_result': words_result,
            'words_result_num': len(words_result),
            'image_status': 'normal',
            'idcard_number_type': 1,
            'message': '识别成功'
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'data': None,
            'message': f'服务器错误: {str(e)}'
        }), 500

@app.route('/api/id_card/health', methods=['GET'])
def health_check() -> Dict[str, Any]:
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'message': '身份证识别 API 服务运行正常'
    }), 200

if __name__ == '__main__':
    # 开发环境配置
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )
