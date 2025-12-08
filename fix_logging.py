#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 report_generator.py 中的日志编码问题
移除日志中包含emoji的输出，避免在Docker/Gunicorn环境中出现latin-1编码错误
"""

def fix_logging_line():
    file_path = 'report_generator.py'
    
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到并替换问题行（大约在第87行）
    target_line = '        logging.info(f"生成的汇总信息文本: {summary_lines}")\r\n'
    replacement_line = '        # 添加调试日志（避免emoji导致编码错误）\r\n        logging.info(f"生成报表 - 日期: {report_date}, 总次数: {total_operations}, 参与人数: {len(report_data)}")\r\n'
    
    modified = False
    new_lines = []
    
    for i, line in enumerate(lines):
        if 'logging.info(f"生成的汇总信息文本:' in line:
            # 找到目标行，替换为新内容
            # 先添加注释行
            new_lines.append('        # 添加调试日志（避免emoji导致编码错误）\r\n')
            # 再添加新的日志行
            new_lines.append('        logging.info(f"生成报表 - 日期: {report_date}, 总次数: {total_operations}, 参与人数: {len(report_data)}")\r\n')
            modified = True
            print(f"✓ 已修复第 {i+1} 行的日志语句")
        else:
            new_lines.append(line)
    
    if modified:
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"\n✓ 文件已成功修改: {file_path}")
        print("修改内容：移除了日志中包含emoji的输出")
        return True
    else:
        print("⚠ 未找到目标行，可能已经被修改过")
        return False

if __name__ == '__main__':
    print("开始修复 report_generator.py 的日志编码问题...")
    print("-" * 50)
    success = fix_logging_line()
    print("-" * 50)
    if success:
        print("\n✅ 修复完成！")
        print("下一步：")
        print("  1. git add report_generator.py")
        print("  2. git commit -m '修复日志编码问题'")
        print("  3. git push")
        print("  4. 在服务器上重新部署")
    else:
        print("\n⚠ 修复可能未成功，请检查文件")
