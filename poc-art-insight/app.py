from flask import Flask, request, jsonify, send_from_directory, render_template_string
from werkzeug.utils import secure_filename
import os
import requests
import json

app = Flask(__name__)

# 配置参数
app.config.update({
    'UPLOAD_FOLDER': 'uploads',
    'LLM_BASE_URL': 'https://api.qnaigc.com/v1',
    'ALLOWED_EXTENSIONS': {'png', 'jpg', 'jpeg'},
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024  # 16MB
})
app.config['LLM_API_KEY'] = os.getenv('LLM_API_KEY', 'default-key')

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def call_vision_llm(prompt, image_url):
    """调用视觉大模型API（根据实际模型文档调整结构）"""
    try:
        # 构造多模态请求结构（示例为doubao-1.5-vision-pro兼容格式）
        data = {
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }],
            "model": "deepseek-v3?search",
            "temperature": 0.7
        }

        response = requests.post(
            f"{app.config['LLM_BASE_URL']}/chat/completions",
            headers={
                "Authorization": f"Bearer {app.config['LLM_API_KEY']}",
                "Content-Type": "application/json"
            },
            json=data,
            timeout=120
        )
        response.raise_for_status()
        
        print("响应内容:", response.text)  # 打印响应内容
        # 检查响应格式
        return response.json()['choices'][0]['message']['content']
    
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP错误: {http_err}")
        print(f"响应内容: {response.text}")
        return f"API调用失败（HTTP错误）: {str(http_err)}"
    except Exception as e:
        print(f"模型调用异常: {str(e)}")
        return f"模型调用异常: {str(e)}"

@app.route('/')
def index():
    """返回增强版前端页面"""
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <title>图片评分系统</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .container { background: #f8f9fa; padding: 25px; border-radius: 12px; box-shadow: 0 2px 15px rgba(0,0,0,0.1); }
                .upload-section { margin-bottom: 30px; padding: 20px; background: white; border-radius: 8px; }
                .preview { max-width: 100%; margin: 15px 0; border-radius: 4px; box-shadow: 0 1px 5px rgba(0,0,0,0.1); }
                .chat-section { background: white; padding: 20px; border-radius: 8px; }
                .chat-history { height: 300px; overflow-y: auto; margin-bottom: 15px; padding: 10px; border: 1px solid #eee; border-radius: 4px; }
                .message { margin: 10px 0; padding: 8px 12px; border-radius: 6px; max-width: 70%; }
                .user-message { background: #e3f2fd; margin-left: auto; }
                .ai-message { background: #f5f5f5; }
                .input-group { display: flex; gap: 10px; }
                #messageInput { flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                button { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; background: #007bff; color: white; transition: background 0.3s; }
                button:hover { background: #0056b3; }
                .upload-result { color: #28a745; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="upload-section">
                    <h3>上传图片</h3>
                    <input type="file" id="fileInput" accept="image/*" onchange="previewImage(this)">
                    <button onclick="uploadFile()">上传图片</button>
                    <div id="uploadResult" class="upload-result"></div>
                    <img id="preview" class="preview" alt="图片预览">
                </div>

                <div class="chat-section">
                    <h3>AI评分对话</h3>
                    <div id="chatHistory" class="chat-history"></div>
                    <div class="input-group">
                        <input type="text" id="messageInput" placeholder="输入评分要求（例如：请从构图和色彩两方面给这张图片打分）">
                        <button onclick="sendMessage()">发送请求</button>
                    </div>
                </div>
            </div>

            <script>
                let currentImageUrl = null;

                function previewImage(input) {
                    if (input.files && input.files[0]) {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            document.getElementById('preview').src = e.target.result;
                        };
                        reader.readAsDataURL(input.files[0]);
                    }
                }

                async function uploadFile() {
                    const fileInput = document.getElementById('fileInput');
                    if (!fileInput.files[0]) {
                        alert('请先选择图片');
                        return;
                    }

                    const formData = new FormData();
                    formData.append('file', fileInput.files[0]);

                    try {
                        const response = await fetch('/upload', {
                            method: 'POST',
                            body: formData
                        });
                        const data = await response.json();
                        
                        if (response.ok) {
                            document.getElementById('uploadResult').textContent = '图片上传成功';
                            currentImageUrl = data.url; // 保存上传后的图片URL
                        } else {
                            alert(`上传失败: ${data.error}`);
                        }
                    } catch (error) {
                        alert(`上传错误: ${error.message}`);
                    }
                }

                async function sendMessage() {
                    const messageInput = document.getElementById('messageInput');
                    const message = messageInput.value.trim();
                    
                    if (!currentImageUrl) {
                        alert('请先上传图片');
                        return;
                    }
                    if (!message) {
                        alert('请输入评分要求');
                        return;
                    }

                    // 显示用户消息
                    const chatHistory = document.getElementById('chatHistory');
                    chatHistory.innerHTML += `<div class="message user-message">${message}</div>`;
                    chatHistory.scrollTop = chatHistory.scrollHeight;

                    // 清空输入框
                    messageInput.value = '';

                    try {
                        const response = await fetch('/api/chat', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                prompt: message,
                                image_url: currentImageUrl
                            })
                        });

                        const data = await response.json();
                        if (response.ok) {
                            chatHistory.innerHTML += `<div class="message ai-message">${data.response}</div>`;
                        } else {
                            chatHistory.innerHTML += `<div class="message ai-message">错误: ${data.error}</div>`;
                        }
                        chatHistory.scrollTop = chatHistory.scrollHeight;
                    } catch (error) {
                        chatHistory.innerHTML += `<div class="message ai-message">请求失败: ${error.message}</div>`;
                        chatHistory.scrollTop = chatHistory.scrollHeight;
                    }
                }
            </script>
        </body>
        </html>
    ''')

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传（增强错误处理）"""
    if 'file' not in request.files:
        return jsonify({'error': '未检测到文件字段'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '仅支持PNG/JPG/JPEG格式'}), 400

    try:
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        return jsonify({
            'message': '上传成功',
            'filename': filename,
            'url': f"{request.host_url}uploads/{filename}"  # 生成完整URL
        })
    except Exception as e:
        return jsonify({'error': f'文件保存失败: {str(e)}'}), 500

@app.route('/uploads/<filename>')
def serve_file(filename):
    """返回上传的文件（添加缓存控制）"""
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        cache_timeout=3600  # 缓存1小时
    )

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    """处理AI评分请求（支持多模态）"""
    data = request.get_json()
    if not data or 'prompt' not in data or 'image_url' not in data:
        return jsonify({'error': '请求需包含prompt和image_url字段'}), 400

    # 验证图片URL有效性（简单检查）
    if not data['image_url'].startswith(f"{request.host_url}uploads/"):
        return jsonify({'error': '无效的图片URL'}), 400

    # 调用视觉大模型
    ai_response = call_vision_llm(data['prompt'], data['image_url'])
    return jsonify({'response': ai_response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    