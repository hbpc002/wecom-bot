#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复文件删除按钮功能
问题：删除按钮的 onclick 事件中，文件名没有正确转义，导致包含特殊字符的文件名会破坏 JavaScript 语法
解决方案：使用 data 属性存储文件名，通过事件监听器处理删除操作
"""

import os
import re

def fix_delete_button():
    """修复 app.js 中的删除按钮功能"""
    
    app_js_path = r'd:\Documents\G-ide\wecom-bot\static\js\app.js'
    
    # 读取文件
    with open(app_js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原文件
    backup_path = app_js_path + '.backup'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ 已备份原文件到: {backup_path}")
    
    # 修复方案1: 修改生成删除按钮的代码，使用 data 属性而不是 onclick
    old_button_code = r'''                        <td>
                            <button class="btn btn-danger btn-sm" onclick="deleteUploadedFile\('(.+?)'\)">删除</button>
                        </td>'''
    
    new_button_code = r'''                        <td>
                            <button class="btn btn-danger btn-sm delete-file-btn" data-filename="${file.filename}">删除</button>
                        </td>'''
    
    # 查找并替换删除按钮生成代码（第407-409行附近）
    pattern1 = r'''(\s+)<td>\s+<button class="btn btn-danger btn-sm" onclick="deleteUploadedFile\('\$\{file\.filename\}'\)">删除</button>\s+</td>'''
    replacement1 = r'''\1<td>
\1    <button class="btn btn-danger btn-sm delete-file-btn" data-filename="${file.filename}">删除</button>
\1</td>'''
    
    content_new = re.sub(pattern1, replacement1, content)
    
    # 修复方案2: 添加事件委托来处理删除按钮点击
    # 在 refreshFilesList 函数之后添加事件监听器
    
    # 查找 deleteUploadedFile 函数的位置
    delete_function_pattern = r'(// 删除已上传的文件\s+async function deleteUploadedFile\(filename\) \{)'
    
    # 在 deleteUploadedFile 函数之前添加事件委托代码
    event_delegation_code = '''// 使用事件委托处理删除按钮点击
document.addEventListener('click', async function(e) {
    if (e.target && e.target.classList.contains('delete-file-btn')) {
        const filename = e.target.getAttribute('data-filename');
        if (filename) {
            await deleteUploadedFile(filename);
        }
    }
});

'''
    
    content_new = re.sub(delete_function_pattern, event_delegation_code + r'\1', content_new)
    
    # 写入修改后的内容
    with open(app_js_path, 'w', encoding='utf-8') as f:
        f.write(content_new)
    
    print(f"✓ 已修复删除按钮功能")
    print(f"✓ 修改内容:")
    print(f"  1. 删除按钮不再使用 onclick 属性")
    print(f"  2. 使用 data-filename 属性存储文件名")
    print(f"  3. 添加事件委托处理删除操作")
    print(f"\n如需恢复原文件，请运行:")
    print(f"  copy {backup_path} {app_js_path}")

if __name__ == '__main__':
    try:
        fix_delete_button()
        print("\n✅ 修复完成！请刷新浏览器页面测试删除功能。")
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
