#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全地注释掉 report_generator.py 中会导致编码问题的日志
只修改特定的行，不使用正则替换
"""

def safe_remove_logging():
    file_path = 'report_generator.py'
    
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified_lines = []
    changes_made = []
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # 第87-88行：生成报表日志
        if 'logging.info(f"生成的汇总信息文本:' in line or 'logging.info(f"生成报表 -' in line:
            modified_lines.append('        pass  # logging removed to avoid emoji encoding errors\r\n')
            changes_made.append(f"第{line_num}行: 注释了生成报表日志")
            continue
        
        # 第152行附近：表格图片保存日志
        if 'logging.info(f"表格图片已保存到:' in line:
            modified_lines.append('            pass  # logging removed to avoid encoding errors\r\n')
            changes_made.append(f"第{line_num}行: 注释了保存图片日志")
            continue
        
        # 字体加载相关日志
        if 'logging.info(f"加载字体:' in line:
            modified_lines.append(line.replace('logging.info(', 'pass  # logging.info('))
            changes_made.append(f"第{line_num}行: 注释了加载字体日志")
            continue
        
        if 'logging.warning(f"字体文件不存在:' in line:
            modified_lines.append(line.replace('logging.warning(', 'pass  # logging.warning('))
            changes_made.append(f"第{line_num}行: 注释了字体不存在警告")
            continue
        
        if 'logging.error(f"加载字体失败:' in line:
            modified_lines.append(line.replace('logging.error(', 'pass  # logging.error('))
            changes_made.append(f"第{line_num}行: 注释了加载字体失败错误")
            continue
        
        if 'logging.info(f"使用fallback字体:' in line:
            modified_lines.append(line.replace('logging.info(', 'pass  # logging.info('))
            changes_made.append(f"第{line_num}行: 注释了fallback字体日志")
            continue
        
        if 'logging.warning("所有字体加载失败' in line:
            modified_lines.append(line.replace('logging.warning(', 'pass  # logging.warning('))
            changes_made.append(f"第{line_num}行: 注释了所有字体失败警告")
            continue
        
        # 其他行保持不变
        modified_lines.append(line)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(modified_lines)
    
    return changes_made

if __name__ == '__main__':
    print("安全地移除可能导致编码问题的日志...")
    print("=" * 60)
    
    changes = safe_remove_logging()
    
    if changes:
        print("\n✅ 已安全地注释以下日志：")
        for change in changes:
            print(f"  • {change}")
    else:
        print("\n⚠️  未找到需要修改的日志行")
    
    print("\n" + "=" * 60)
    print("修改完成！")
    print("\n请测试运行: python web_server.py")
    print("如果正常，再提交代码")
