#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复 main.py 中的 emoji 编码问题 - 方式2
"""

def fix_method_2():
    """修复方式2中的文件名问题"""
    
    # 读取文件
    with open('main.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 备份
    with open('main.py.backup_method2', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    # 查找并修改第360行
    modified = False
    for i, line in enumerate(lines):
        if 'Content-Disposition: form-data; name="media"; filename="{os.path.basename(image_path)}"' in line:
            # 在这一行之前插入安全文件名处理
            indent = '                '
            if i > 0 and 'boundary =' in lines[i-2]:
                # 在 boundary 定义后面,body 定义之前插入
                insert_lines = [
                    f'{indent}# 使用安全的文件名（移除可能的emoji等特殊字符）\n',
                    f'{indent}safe_filename = os.path.basename(image_path).encode(\'ascii\', \'ignore\').decode(\'ascii\')\n',
                    f'{indent}if not safe_filename:\n',
                    f'{indent}    safe_filename = \'image.jpg\' if file_extension in [\'.jpg\', \'.jpeg\'] else \'image.png\'\n',
                    f'{indent}\n'
                ]
                # 插入新行
                for j, new_line in enumerate(insert_lines):
                    lines.insert(i + j, new_line)
                
                # 修改 Content-Disposition 行
                lines[i + len(insert_lines)] = line.replace(
                    '{os.path.basename(image_path)}',
                    '{safe_filename}'
                )
                modified = True
                break
    
    if modified:
        # 写入修改
        with open('main.py', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("✓ 方式2修复完成!")
    else:
        print("✗ 未找到需要修复的代码")

if __name__ == '__main__':
    fix_method_2()
