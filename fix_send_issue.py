#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复发送到生产环境的问题
1. 移除不必要的确认对话框（因为用户说没有点击取消）
2. 添加持久化的成功提示，不会一闪而过
"""

import os
import shutil
from datetime import datetime

# 文件路径
APP_JS_PATH = r'd:\Documents\G-ide\wecom-bot\static\js\app.js'
INDEX_HTML_PATH = r'd:\Documents\G-ide\wecom-bot\templates\index.html'

# 备份文件
backup_js = APP_JS_PATH + f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
shutil.copy2(APP_JS_PATH, backup_js)
print(f"✓ 已备份 app.js 到: {backup_js}")

# 读取当前的 app.js
with open(APP_JS_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到 sendToWecom 函数并替换
new_send_function = '''async function sendToWecom(env) {
    const dateInput = document.getElementById('wecomDate');
    const date = dateInput.value;

    if (!date) {
        showNotification('请先选择日期', 'error');
        return;
    }

    const envName = env === 'test' ? '测试环境' : '生产环境';
    
    const btn = env === 'test' ? document.getElementById('sendTestBtn') : document.getElementById('sendProdBtn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span>⏳</span> 发送中...';
    
    console.log(`开始发送到${envName}，日期: ${date}`);

    try {
        const response = await fetch('/api/send-to-wecom', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ date, env })
        });

        console.log('收到响应:', response.status);
        const data = await response.json();
        console.log('响应数据:', data);

        if (data.success) {
            showNotification(`✅ ${data.message}`, 'success');
            console.log('发送成功:', data.message);
        } else {
            showNotification(`❌ 发送失败：${data.error}`, 'error');
            console.error('发送失败:', data.error);
        }
    } catch (error) {
        console.error('发送异常:', error);
        showNotification(`❌ 发送失败：${error.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
        console.log('发送操作结束');
    }
}'''

# 添加通知函数
notification_function = '''
// 显示通知消息
function showNotification(message, type = 'info') {
    // 移除已存在的通知
    const existingNotification = document.querySelector('.custom-notification');
    if (existingNotification) {
        existingNotification.remove();
    }

    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `custom-notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // 3秒后自动消失
    setTimeout(() => {
        if (notification.parentElement) {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}
'''

# 查找并替换 sendToWecom 函数
import re

# 找到函数定义的开始和结束
pattern = r'async function sendToWecom\(env\) \{.*?^\}'
match = re.search(pattern, content, re.MULTILINE | re.DOTALL)

if match:
    content = content[:match.start()] + new_send_function + content[match.end():]
    print("✓ 已替换 sendToWecom 函数")
else:
    print("✗ 未找到 sendToWecom 函数")

# 在文件末尾添加通知函数（如果不存在）
if 'showNotification' not in content:
    # 在最后一个函数之前插入
    content = notification_function + '\n' + content
    print("✓ 已添加 showNotification 函数")

# 写入修改后的内容
with open(APP_JS_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✓ 已更新 app.js 文件")

# 现在添加CSS样式
CSS_PATH = r'd:\Documents\G-ide\wecom-bot\static\css\style.css'
backup_css = CSS_PATH + f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
shutil.copy2(CSS_PATH, backup_css)
print(f"✓ 已备份 style.css 到: {backup_css}")

notification_css = '''
/* 自定义通知样式 */
.custom-notification {
    position: fixed;
    top: 20px;
    right: 20px;
    min-width: 300px;
    max-width: 500px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 10000;
    animation: slideIn 0.3s ease-out;
}

.custom-notification.success {
    border-left: 4px solid #4CAF50;
}

.custom-notification.error {
    border-left: 4px solid #f44336;
}

.custom-notification.info {
    border-left: 4px solid #2196F3;
}

.notification-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
}

.notification-message {
    flex: 1;
    font-size: 14px;
    color: #333;
    line-height: 1.5;
}

.notification-close {
    background: none;
    border: none;
    font-size: 24px;
    color: #999;
    cursor: pointer;
    padding: 0;
    margin-left: 16px;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: color 0.2s;
}

.notification-close:hover {
    color: #333;
}

.custom-notification.fade-out {
    animation: slideOut 0.3s ease-out forwards;
}

@keyframes slideIn {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOut {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(400px);
        opacity: 0;
    }
}
'''

# 读取CSS文件
with open(CSS_PATH, 'r', encoding='utf-8') as f:
    css_content = f.read()

# 如果不存在通知样式，则添加
if 'custom-notification' not in css_content:
    css_content += '\n' + notification_css
    with open(CSS_PATH, 'w', encoding='utf-8') as f:
        f.write(css_content)
    print("✓ 已添加通知样式到 style.css")
else:
    print("ℹ️ 通知样式已存在")

print("\n修复完成！")
print("\n主要改进:")
print("  1. 移除了生产环境的确认对话框")
print("  2. 使用自定义通知替代 alert，消息会显示5秒")
print("  3. 用户可以手动关闭通知")
print("  4. 通知有滑入滑出动画效果")
print("\n请刷新浏览器页面查看效果")
