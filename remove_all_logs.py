#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移除 report_generator.py 中所有可能导致编码问题的日志语句
"""
import re

def remove_problematic_logging():
    file_path = 'report_generator.py'
    
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 记录修改
    modifications = []
    
    # 移除或注释掉包含中文、emoji的日志
    # 1. 移除 "生成的汇总信息文本" 相关的日志
    if 'logging.info(f"生成的汇总信息文本:' in content or 'logging.info(f"生成报表 -' in content:
        # 使用正则表达式注释掉这一行
        content = re.sub(
            r'(\s*)logging\.info\(f"生成.*?"\)\r?\n',
            r'\1# logging.info removed to avoid encoding errors\r\n',
            content
        )
        modifications.append("移除了'生成报表'相关的日志")
    
    # 2. 移除 "表格图片已保存到" 相关的日志（包含中文路径）
    if '表格图片已保存到' in content:
        content = re.sub(
            r'(\s*)logging\.info\(f"表格图片已保存到:.*?"\)\r?\n',
            r'\1# logging.info removed to avoid encoding errors\r\n',
            content
        )
        modifications.append("移除了'表格图片已保存到'日志")
    
    # 3. 处理 "加载字体" 相关日志（路径可能包含中文）
    content = re.sub(
        r'(\s*)logging\.info\(f"加载字体:.*?"\)\r?\n',
        r'\1# logging.info removed to avoid encoding errors\r\n',
        content
    )
    modifications.append("移除了'加载字体'相关日志")
    
    content = re.sub(
        r'(\s*)logging\.info\(f"使用fallback字体:.*?"\)\r?\n',
        r'\1# logging.info removed to avoid encoding errors\r\n',
        content
    )
    
    # 4. 处理警告日志
    content = re.sub(
        r'(\s*)logging\.warning\(f"字体文件不存在:.*?"\)\r?\n',
        r'\1# logging.warning removed to avoid encoding errors\r\n',
        content
    )
    
    content = re.sub(
        r'(\s*)logging\.error\(f"加载字体失败:.*?"\)\r?\n',
        r'\1# logging.error removed to avoid encoding errors\r\n',
        content
    )
    
    content = re.sub(
        r'(\s*)logging\.warning\("所有字体加载失败.*?"\)\r?\n',
        r'\1# logging.warning removed to avoid encoding errors\r\n',
        content
    )
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return modifications

if __name__ == '__main__':
    print("开始移除 report_generator.py 中可能导致编码问题的日志...")
    print("=" * 60)
    
    mods = remove_problematic_logging()
    
    print("\n✅ 完成！已注释/移除以下日志：")
    for mod in mods:
        print(f"  • {mod}")
    
    print("\n" + "=" * 60)
    print("所有可能导致编码错误的日志已被移除")
    print("\n下一步：")
    print("  1. 检查文件确认修改正确")
    print("  2. git add report_generator.py")
    print("  3. git commit -m '移除所有可能导致编码问题的日志'")
    print("  4. git push")
