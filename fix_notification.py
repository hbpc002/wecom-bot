#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 showNotification 函数未定义的问题
"""

import os

APP_JS_PATH = r'd:\Documents\G-ide\wecom-bot\static\js\app.js'

# 读取当前文件
with open(APP_JS_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# showNotification 函数定义
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
    
    // 5秒后自动消失
    setTimeout(() => {
        if (notification.parentElement) {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}
'''

# 检查是否已存在
if 'function showNotification' not in content:
    # 在 formatFileSize 函数之后添加
    if 'function formatFileSize(bytes)' in content:
        # 找到 formatFileSize 函数的结束位置
        lines = content.split('\n')
        insert_index = -1
        in_format_function = False
        brace_count = 0
        
        for i, line in enumerate(lines):
            if 'function formatFileSize(bytes)' in line:
                in_format_function = True
                brace_count = 0
            
            if in_format_function:
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0 and '}' in line:
                    insert_index = i + 1
                    break
        
        if insert_index > 0:
            lines.insert(insert_index, notification_function)
            content = '\n'.join(lines)
            print("✓ 已在 formatFileSize 函数后添加 showNotification 函数")
        else:
            # 如果找不到合适位置，添加到文件开头
            content = notification_function + '\n' + content
            print("✓ 已在文件开头添加 showNotification 函数")
    else:
        # 添加到文件开头
        content = notification_function + '\n' + content
        print("✓ 已在文件开头添加 showNotification 函数")
    
    # 写入文件
    with open(APP_JS_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ 文件已更新")
else:
    print("ℹ️ showNotification 函数已存在")

print("\n请刷新浏览器页面（Ctrl+F5）")
