#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复 main.py 中的 emoji 编码问题
将文件名中的 emoji 字符清理掉,避免在 HTTP 请求中使用 latin-1 编码时出错
"""

import re

def fix_emoji_encoding():
    """修复 main.py 中的 emoji 编码问题"""
    
    # 读取文件
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原文件
    with open('main.py.backup_emoji_fix', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 修复方式1: 在 files 参数中使用安全的文件名
    old_pattern_1 = r"""            # 尝试多种上传方式
            # 方式1：使用files参数
            try:
                files = \{
                    'media': \(os\.path\.basename\(image_path\), file_data, mime_type\)
                \}
                
                upload_response = self\.session\.post\(
                    upload_url,
                    files=files,
                    timeout=10,
                    headers=\{'User-Agent': 'Mozilla/5\.0 \(Windows NT 10\.0; Win64; x64\) AppleWebKit/537\.36'\}
                \)"""
    
    new_pattern_1 = """            # 尝试多种上传方式
            # 方式1：使用files参数
            try:
                # 使用安全的文件名（移除可能的emoji等特殊字符）
                safe_filename = os.path.basename(image_path).encode('ascii', 'ignore').decode('ascii')
                if not safe_filename:
                    safe_filename = 'image.jpg' if file_extension in ['.jpg', '.jpeg'] else 'image.png'
                
                files = {
                    'media': (safe_filename, file_data, mime_type)
                }
                
                upload_response = self.session.post(
                    upload_url,
                    files=files,
                    timeout=10,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )"""
    
    content = re.sub(old_pattern_1, new_pattern_1, content, flags=re.MULTILINE)
    
    # 修复方式2: 在 Content-Disposition 中使用安全的文件名
    old_pattern_2 = r"""            # 方式2：使用data参数
            try:
                # 构建multipart/form-data
                boundary = '----WebKitFormBoundary' \+ ''\.join\(\['0123456789ABCDEF'\]\[int\(x\)\] for x in os\.urandom\(16\)\)
                
                body = \(
                    f'--\{boundary\}\\\\r\\\\n'
                    f'Content-Disposition: form-data; name="media"; filename="\{os\.path\.basename\(image_path\)\}"\\\\r\\\\n'
                    f'Content-Type: \{mime_type\}\\\\r\\\\n\\\\r\\\\n'
                \)\.encode\('utf-8'\)
                body \+= file_data
                body \+= f'\\\\r\\\\n--\{boundary\}--\\\\r\\\\n'\.encode\('utf-8'\)"""
    
    new_pattern_2 = """            # 方式2：使用data参数
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
                ).encode('utf-8')
                body += file_data
                body += f'\\r\\n--{boundary}--\\r\\n'.encode('utf-8')"""
    
    content = re.sub(old_pattern_2, new_pattern_2, content, flags=re.MULTILINE)
    
    # 写入修改后的文件
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ 修复完成!")
    print("  - 已备份原文件到: main.py.backup_emoji_fix")
    print("  - 已修复 emoji 编码问题")
    print("\n修复内容:")
    print("  1. 在方式1中,文件名会先清理掉 emoji 字符")
    print("  2. 在方式2中,Content-Disposition 头部使用清理后的文件名")
    print("\n这样可以避免 'latin-1' codec can't encode character 错误")

if __name__ == '__main__':
    fix_emoji_encoding()
