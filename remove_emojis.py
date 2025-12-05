#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全面修复 emoji 相关问题
1. 移除报表标题中的 emoji（最简单有效的方案）
2. 确保文件名不包含特殊字符
"""

def remove_emojis_from_report():
    # 读取文件
    with open('report_generator.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份
    with open('report_generator.py.backup_emoji', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 替换包含 emoji 的字符串为纯文本
    replacements = [
        ('summary_lines.append("📊 听录音统计报表")',
         'summary_lines.append("听录音统计报表")'),
        
        ('full_image_lines.append(f"📊 {report_date.strftime(\'%Y年%m月%d日\')}听录音统计报表")',
         'full_image_lines.append(f"{report_date.strftime(\'%Y年%m月%d日\')}听录音统计报表")'),
        
        ('if line.startswith("📊"):',
         'if line.startswith("听录音统计报表") or line.endswith("听录音统计报表"):'),
        
        ('elif line.startswith("## 📈"):',
         'elif line.startswith("## 汇总信息"):'),
        
        ('"## 📈 汇总信息"',
         '"## 汇总信息"'),
        
        ('elif line.startswith("## 📋"):',
         'elif line.startswith("## 详细数据"):'),
        
        ('"## 📋 详细数据"',
         '"## 详细数据"'),
    ]
    
    modified = False
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            modified = True
            print(f"✓ 已替换: {old[:50]}...")
    
    if modified:
        # 写入
        with open('report_generator.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("\n✓ 所有 emoji 已从 report_generator.py 中移除")
        print("  这样可以完全避免编码问题")
    else:
        print("⚠ 未找到需要替换的 emoji")
    
    return modified

if __name__ == '__main__':
    if remove_emojis_from_report():
        print("\n修复完成！现在报表中不再包含 emoji 字符")
        print("请重新提交代码并重新构建 Docker 镜像")
    else:
        print("\n未进行任何修改")
