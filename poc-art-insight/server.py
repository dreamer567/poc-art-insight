from flask import Flask, request, jsonify, send_from_directory, render_template_string
from werkzeug.utils import secure_filename
import os
import json
    
# import openai
# from openai import OpenAIError, APIError, APIConnectionError, Timeout

app = Flask(__name__)

# 配置参数
app.config.update({
    'UPLOAD_FOLDER': 'uploads',
    # 'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB
    'LLM_BASE_URL': 'https://api.qnaigc.com/v1/chat/completions',
})
app.config['LLM_API_KEY'] = os.getenv('LLM_API_KEY', 'default-key')

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and  filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

import requests
def call_deepseek(prompt):

    url = "https://api.qnaigc.com/v1/chat/completions"

    payload = {
        "stream": False,
        "model": "doubao-1.5-vision-pro",        
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请帮我根据色调（包括色相、明度和纯度），空间（透视、景深和虚实效果），体积（块面、光影和质感的表示方式）和节奏（交融、对比和变化）给图片评分并整理一份报告给我."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "http://swei02p5t.hd-bkt.clouddn.com/sample/color.jpg"
                        }
                    }
                ]
            }
        ]
    }
    headers = {
        "Authorization": "Bearer sk-a01996924f84ee46c7fb19c209778896ef87f40ec8c618e4355c285bcc873adc",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    print(response.json())
    # print(response.text)  # 打印响应内容
    # 检查响应格式
    return response.json()['choices'][0]['message']['content']

from flask import Flask, request, jsonify, send_from_directory, render_template_string  

# from openai import OpenAI

# def call_deepseek1(prompt):
#     print("调用DeepSeek API，参数:", prompt)  # 调试信息
#     # prompt="hello"
#     # 构建包含变量的Python字典
#     # json_data = [{"role": "user", "content": prompt}]

#     # 转换为JSON字符串（确保中文等特殊字符正确显示）
#     # json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
#     # json_str = '''{
#     #     "messages": [{"role": "user", "content": "how are you?"}],
#     #     "model": "deepseek-v3"
#     # }'''

#     # 打印合法的JSON格式
#     # print("请求的JSON参数:", json_str)
#     llm_api_key = app.config['LLM_API_KEY']  # 替换为你的 API Key 配置
#     url = app.config['LLM_BASE_URL']  # 替换为你的 API 基础 URL（如非默认）
#     model_llm="deepseek-v3"
 
#     # url = 'https://api.qnaigc.com/v1/'
#     # llm_api_key = 'your llm_api_key'

#     client = OpenAI(
#         base_url=url,
#         api_key=llm_api_key
#     )

#     # 发送非流式输出的请求
#     messages = [
#         {"role": "user", "content": prompt}
#     ]
#     print("请求的消息:", messages)  # 调试信息
#     response = client.chat.completions.create(
#         model=model_llm,
#         messages=messages,
#         stream=False, 
#         max_tokens=4096
#     )
#     print("响应的消息:", response)  # 调试信息
#     # 检查响应格式
#     content = response.choices[0].message.content
#     print(content)

#     return content

#     # # Round 2
#     # messages.append({"role": "assistant", "content": content})
#     # messages.append({'role': 'user', 'content': "继续"})
#     # response = client.chat.completions.create(
#     #     model=model_llm,
#     #     messages=messages,
#     #     stream=False
#     # )
#     # content = response.choices[0].message.content
#     # print(content)

    
@app.route('/')
def index():
    """返回前端页面"""
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>MCP客户端</title>
            <link rel="stylesheet" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <div class="upload-section">
                    <h3>图片上传</h3>
                    <input type="file" id="fileInput" accept="image/*">
                    <button onclick="uploadFile()">上传</button>
                    <div id="uploadResult"></div>
                    <img id="preview" class="preview" />
                </div>

                <div class="chat-section">
                    <h3>AI对话</h3>
                    <div id="chatHistory"></div>
                    <div class="input-group">
                        <input type="text" id="messageInput" placeholder="输入问题...">
                        <button onclick="sendMessage()">发送</button>
                    </div>
                </div>
            </div>
            <script src="/static/script.js"></script>
        </body>
        </html>
    ''')

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        return jsonify({
            'message': '上传成功',
            'filename': filename,
            'url': f"/uploads/{filename}"
        })
    else:
        return jsonify({'error': '仅支持PNG/JPG/JPEG格式'}), 400

@app.route('/uploads/<filename>')
def serve_file(filename):
    """返回上传的文件"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    """处理AI对话"""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': '无效请求'}), 400
    
    ai_response = call_deepseek(data['message'])
    return jsonify({'response': ai_response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)