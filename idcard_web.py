# coding: utf-8
# 网页服务器 - 提供前端页面和代理 API

from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

# 后端 API 地址
BACKEND_API = 'http://localhost:5000/api/id_card/recognize'

# HTML 页面内容
HTML_CONTENT = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>身份证识别系统</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", "PingFang SC", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            max-width: 600px;
            width: 100%;
            padding: 40px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #999;
            font-size: 14px;
        }
        
        .upload-section {
            margin-bottom: 30px;
        }
        
        .upload-label {
            display: block;
            color: #333;
            font-weight: 600;
            margin-bottom: 12px;
            font-size: 16px;
        }
        
        .upload-box {
            position: relative;
            border: 2px dashed #667eea;
            border-radius: 8px;
            padding: 40px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            background: #f9f9f9;
        }
        
        .upload-box:hover {
            background: #f0f2ff;
            border-color: #764ba2;
        }
        
        .upload-box.dragover {
            background: #e8ebff;
            border-color: #764ba2;
        }
        
        .upload-box input {
            display: none;
        }
        
        .upload-icon {
            font-size: 40px;
            margin-bottom: 10px;
        }
        
        .upload-text {
            color: #666;
            font-size: 14px;
            line-height: 1.5;
        }
        
        .upload-text .highlight {
            color: #667eea;
            font-weight: 600;
        }
        
        .preview-section {
            display: none;
            margin-bottom: 20px;
            padding: 15px;
            background: #f9f9f9;
            border-radius: 8px;
            text-align: center;
        }
        
        .preview-section.show {
            display: block;
        }
        
        .preview-image {
            max-width: 100%;
            max-height: 300px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        
        .preview-filename {
            color: #999;
            font-size: 12px;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
        }
        
        .btn {
            flex: 1;
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn-submit {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-submit:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn-submit:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .btn-clear {
            background: #f0f0f0;
            color: #666;
        }
        
        .btn-clear:hover {
            background: #e0e0e0;
        }
        
        .response-section {
            display: none;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .response-section.show {
            display: block;
        }
        
        .response-section.error {
            background: #fff3cd;
            border-left-color: #ff6b6b;
        }
        
        .response-section.success {
            background: #d4edda;
            border-left-color: #51cf66;
        }
        
        .response-title {
            font-weight: 600;
            margin-bottom: 12px;
            color: #333;
            font-size: 16px;
        }
        
        .response-section.success .response-title {
            color: #155724;
        }
        
        .response-section.error .response-title {
            color: #856404;
        }
        
        .json-box {
            background: white;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #ddd;
            overflow-x: auto;
            font-family: "Monaco", "Courier New", monospace;
            font-size: 13px;
            line-height: 1.6;
            color: #333;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .json-box pre {
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .result-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(0, 0, 0, 0.1);
        }
        
        .result-item:last-child {
            border-bottom: none;
        }
        
        .result-label {
            font-weight: 600;
            color: #666;
        }
        
        .result-value {
            color: #333;
            word-break: break-all;
            text-align: right;
            flex: 1;
            margin-left: 20px;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .loading.show {
            display: block;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .loading-text {
            color: #666;
            font-size: 14px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .status-success {
            background: #d4edda;
            color: #155724;
        }
        
        .status-error {
            background: #f8d7da;
            color: #721c24;
        }
        
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #999;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 身份证识别系统</h1>
            <p>上传身份证照片，自动识别姓名和身份证号</p>
        </div>
        
        <div class="upload-section">
            <label class="upload-label">上传身份证照片</label>
            <div class="upload-box" id="uploadBox">
                <input type="file" id="fileInput" accept="image/*">
                <div class="upload-icon">📤</div>
                <div class="upload-text">
                    <p>点击选择或拖拽图片到这里</p>
                    <p class="highlight">支持 JPG、PNG、WEBP 等格式</p>
                </div>
            </div>
        </div>
        
        <div class="preview-section" id="previewSection">
            <img id="previewImage" class="preview-image" src="" alt="预览">
            <div class="preview-filename" id="previewFilename"></div>
        </div>
        
        <div class="button-group">
            <button class="btn btn-submit" id="submitBtn" disabled>
                🚀 识别身份证
            </button>
            <button class="btn btn-clear" id="clearBtn">
                🗑️ 清空
            </button>
        </div>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <div class="loading-text">正在识别中，请稍候...</div>
        </div>
        
        <div class="response-section" id="responseSection">
            <div class="status-badge" id="statusBadge"></div>
            <div class="response-title" id="responseTitle"></div>
            <div id="responseContent"></div>
        </div>
        
        <div class="footer">
            <p>API 服务: <span id="apiStatus">✓ 连接正常</span></p>
            <p>© 2026 速光网络软件开发 suguang.cc 抖音：dubaishun12 | 使用 CnOCR 技术</p>
        </div>
    </div>

    <script>
        const uploadBox = document.getElementById('uploadBox');
        const fileInput = document.getElementById('fileInput');
        const submitBtn = document.getElementById('submitBtn');
        const clearBtn = document.getElementById('clearBtn');
        const previewSection = document.getElementById('previewSection');
        const previewImage = document.getElementById('previewImage');
        const previewFilename = document.getElementById('previewFilename');
        const loading = document.getElementById('loading');
        const responseSection = document.getElementById('responseSection');
        const apiStatusEl = document.getElementById('apiStatus');
        
        let selectedFile = null;
        
        // 上传框点击
        uploadBox.addEventListener('click', () => fileInput.click());
        
        // 文件选择
        fileInput.addEventListener('change', handleFileSelect);
        
        // 拖拽上传
        uploadBox.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadBox.classList.add('dragover');
        });
        
        uploadBox.addEventListener('dragleave', () => {
            uploadBox.classList.remove('dragover');
        });
        
        uploadBox.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadBox.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFileSelect();
            }
        });
        
        // 处理文件选择
        function handleFileSelect() {
            const file = fileInput.files[0];
            if (!file) return;
            
            if (!file.type.startsWith('image/')) {
                alert('请选择图片文件');
                return;
            }
            
            selectedFile = file;
            submitBtn.disabled = false;
            
            // 显示预览
            const reader = new FileReader();
            reader.onload = (e) => {
                previewImage.src = e.target.result;
                previewFilename.textContent = file.name;
                previewSection.classList.add('show');
            };
            reader.readAsDataURL(file);
        }
        
        // 清空
        clearBtn.addEventListener('click', () => {
            fileInput.value = '';
            selectedFile = null;
            submitBtn.disabled = true;
            previewSection.classList.remove('show');
            responseSection.classList.remove('show');
        });
        
        // 提交识别
        submitBtn.addEventListener('click', async () => {
            if (!selectedFile) return;
            
            submitBtn.disabled = true;
            loading.classList.add('show');
            responseSection.classList.remove('show');
            
            try {
                const formData = new FormData();
                formData.append('image', selectedFile);
                
                const response = await fetch('/api/recognize', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                displayResponse(result);
                
            } catch (error) {
                displayResponse({
                    success: false,
                    message: '请求失败: ' + error.message
                });
            } finally {
                loading.classList.remove('show');
                submitBtn.disabled = false;
            }
        });
        
        // 显示响应
        function displayResponse(data) {
            responseSection.classList.add('show');
            
            if (data.success) {
                responseSection.classList.add('success');
                responseSection.classList.remove('error');
                document.getElementById('statusBadge').className = 'status-badge status-success';
                document.getElementById('statusBadge').textContent = '✓ 识别成功';
                document.getElementById('responseTitle').textContent = '识别结果';
                
                const resultData = data.data || {};
                const html = `
                    <div class="result-item">
                        <span class="result-label">姓名</span>
                        <span class="result-value">${resultData.name || '未识别'}</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">身份证号</span>
                        <span class="result-value">${resultData.id_number || '未识别'}</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">置信度</span>
                        <span class="result-value">${(resultData.confidence * 100).toFixed(2)}%</span>
                    </div>
                    <hr style="margin: 15px 0; border: none; border-top: 1px solid rgba(0,0,0,0.1);">
                    <div style="margin-top: 15px;">
                        <div style="font-weight: 600; margin-bottom: 10px; color: #666;">完整 JSON 响应:</div>
                        <div class="json-box">
                            <pre>${JSON.stringify(data, null, 2)}</pre>
                        </div>
                    </div>
                `;
                document.getElementById('responseContent').innerHTML = html;
            } else {
                responseSection.classList.add('error');
                responseSection.classList.remove('success');
                document.getElementById('statusBadge').className = 'status-badge status-error';
                document.getElementById('statusBadge').textContent = '✗ 识别失败';
                document.getElementById('responseTitle').textContent = '错误信息';
                
                const html = `
                    <p style="color: #721c24; margin-bottom: 15px;">${data.message || '未知错误'}</p>
                    <div style="font-weight: 600; margin-bottom: 10px; color: #666;">完整响应:</div>
                    <div class="json-box">
                        <pre>${JSON.stringify(data, null, 2)}</pre>
                    </div>
                `;
                document.getElementById('responseContent').innerHTML = html;
            }
        }
        
        // 检查 API 状态
        async function checkApiStatus() {
            try {
                const response = await fetch('/api/health');
                if (response.ok) {
                    apiStatusEl.textContent = '✓ 连接正常';
                } else {
                    apiStatusEl.textContent = '✗ API 异常';
                }
            } catch (error) {
                apiStatusEl.textContent = '✗ 无法连接';
            }
        }
        
        // 页面加载时检查 API
        checkApiStatus();
        setInterval(checkApiStatus, 10000); // 每 10 秒检查一次
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """首页"""
    return HTML_CONTENT

@app.route('/api/recognize', methods=['POST'])
def recognize():
    """识别接口 - 代理到后端 API"""
    try:
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'message': '未提供图片文件'
            }), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '文件名为空'
            }), 400
        
        # 将文件转发到后端 API
        files = {'image': file}
        response = requests.post(BACKEND_API, files=files, timeout=30)
        
        return jsonify(response.json()), response.status_code
    
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'message': '后端服务处理超时'
        }), 504
    
    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'message': '无法连接到后端 API 服务'
        }), 503
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'处理失败: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    try:
        response = requests.get('http://localhost:5000/api/id_card/health', timeout=5)
        if response.ok:
            return jsonify({'status': 'healthy'}), 200
        else:
            return jsonify({'status': 'unhealthy'}), 503
    except:
        return jsonify({'status': 'unhealthy'}), 503

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("身份证识别系统 - 网页服务")
    print("=" * 60)
    print("\n✓ 服务启动成功")
    print("📱 访问地址: http://localhost:3000")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=3000, debug=False, threaded=True)
