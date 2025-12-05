#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
恢复中文内容，同时修复编码问题
策略：确保所有文件操作和HTTP操作都正确处理UTF-8编码
"""

def restore_chinese_and_fix_encoding():
    # 读取文件
    with open('report_generator.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份
    with open('report_generator.py.backup_restore', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 恢复中文内容
    replacements = [
        ('full_image_lines.append(f"{report_date.strftime(\'%Y-%m-%d\')} Call Recording Report")',
         'full_image_lines.append(f"{report_date.year}年{report_date.month}月{report_date.day}日 听录音统计报表")'),
        
        ('"## Summary"',
         '"## 汇总信息"'),
        
        ('"## Details"',
         '"## 详细数据"'),
        
        ('"- **Total Recordings**:',
         '"- **总听录音次数**:'),
        
        ('"- **Participants**:',
         '"- **参与人数**:'),
        
        ('"- **Average Recordings per Person**:',
         '"- **平均每人听录音次数**:'),
        
        ('if line.startswith("听录音统计报表") or line.endswith("听录音统计报表"):',
         'if "听录音统计报表" in line and not line.startswith("##"):'),
        
        ('elif line.startswith("## 汇总信息"):',
         'elif line.startswith("## 汇总信息"):'),
        
        ('elif line.startswith("## 详细数据"):',
         'elif line.startswith("## 详细数据"):'),
    ]
    
    modified = False
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            modified = True
            print(f"✓ 已替换为中文")
    
    if modified:
        # 写入
        with open('report_generator.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("\n✓ 已恢复中文内容")
    
    return modified

if __name__ == '__main__':
    restore_chinese_and_fix_encoding()
    print("\n现在需要确保 PIL 正确处理 UTF-8")
    print("关键修复：避免在 strftime 中使用中文，改用 f-string 组合")
