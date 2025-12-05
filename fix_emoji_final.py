#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复 main.py 中的 emoji 编码问题 - 完整版本
"""

def fix_main_py():
    # 读取整个文件
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份
    with open('main.py.backup_final', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 修复1: files参数中使用 os.path.basename(image_path)
    content = content.replace(
        """            # 尝试多种上传方式
            # 方式1：使用files参数
            try:
                files = {
                    'media': (os.path.basename(image_path), file_data, mime_type)
                }""",
        """            # 尝试多种上传方式
            # 方式1：使用files参数
            try:
                # 使用安全的文件名（移除可能的emoji等特殊字符）
                safe_filename = os.path.basename(image_path).encode('ascii', 'ignore').decode('ascii')
                if not safe_filename:
                    safe_filename = 'image.jpg' if file_extension in ['.jpg', '.jpeg'] else 'image.png'
                
                files = {
                    'media': (safe_filename, file_data, mime_type)
                }"""
    )
    
    # 修复2: Content-Disposition中使用 os.path.basename(image_path)
    content = content.replace(
        """            # 方式2：使用data参数
            try:
                # 构建multipart/form-data
                boundary = '----WebKitFormBoundary' + ''.join(['0123456789ABCDEF'][int(x)] for x in os.urandom(16))
                
                body = (
                    f'--{boundary}\\r\\n'
                    f'Content-Disposition: form-data; name="media"; filename="{os.path.basename(image_path)}"\\r\\n'
                    f'Content-Type: {mime_type}\\r\\n\\r\\n'
                ).encode('utf-8')""",
        """            # 方式2：使用data参数
            try:
                # 使用安全的文件名（移除可能的emoji等特殊字符）
                safe_filename = os.path.basename(image_path).encode('ascii', 'ignore').decode('ascii')
                if not safe_filename:
                    safe_filename = 'image.jpg' if file_extension in ['.jpg', '.jpeg'] else 'image.png'
                
                # 构建multipart/form-data
                boundary = '----WebKitFormBoundary' + ''.join(['0123456789ABCDEF'][int(x)] for x in os.urandom(16))
                
                body = (
                    f'--{boundary}\\r\\n'
                    f'Content-Disposition: form-data; name="media"; filename="{safe_filename}"\\r\\n'
                    f'Content-Type: {mime_type}\\r\\n\\r\\n'
                ).encode('utf-8')"""
    )
    
    # 写入
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ 修复完成!")
    print("已修复emoji编码问题,避免 'latin-1' codec 错误")

if __name__ == '__main__':
    fix_main_py()
