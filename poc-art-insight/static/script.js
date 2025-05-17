// 文件上传逻辑
async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const resultDiv = document.getElementById('uploadResult');
    const preview = document.getElementById('preview');
    
    if (!fileInput.files[0]) {
        resultDiv.innerHTML = '<span class="error-msg">请选择文件</span>';
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
            preview.src = data.url;
            resultDiv.innerHTML = `
                <span class="success-msg">✓ \(  {data.message}</span>
                <p>文件名:   \){data.filename}</p>
            `;
        } else {
            resultDiv.innerHTML = `<span class="error-msg">错误: \(  {data.error}</span>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<span class="error-msg">请求失败:   \){error.message}</span>`;
    }
}

// 聊天功能逻辑
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const chatHistory = document.getElementById('chatHistory');
    
    const userMessage = messageInput.value.trim();
    if (!userMessage) {
        alert('请输入问题');
        return;
    }

    // 显示用户消息
    chatHistory.innerHTML += `<div class="user-msg">我: ${userMessage}</div>`;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: userMessage })
        });

        const data = await response.json();

        if (response.ok) {
            // 显示AI回复
            chatHistory.innerHTML += `<div class="bot-msg">AI: ${data.response}</div>`;
        } else {
            chatHistory.innerHTML += `<div class="error-msg">错误: ${data.error || '未知错误'}</div>`;
        }
    } catch (error) {
        chatHistory.innerHTML += `<div class="error-msg">请求失败: ${error.message}</div>`;
    }

    // 清空输入框并滚动到底部
    messageInput.value = '';
    chatHistory.scrollTop = chatHistory.scrollHeight;
}