#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复脚本：为报表添加月累计列功能

此脚本将修改以下文件：
1. main.py - 在生成报表时传递月累计数据
2. web_server.py - 在手动发送报表时传递月累计数据  
3. report_generator.py - 修改报表生成逻辑以支持月累计列
"""

import os
import re

def backup_file(filepath):
    """备份文件"""
    backup_path = filepath + '.backup'
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已备份: {filepath} -> {backup_path}")
        return True
    return False

def fix_main_py():
    """修复 main.py"""
    filepath = 'd:/Documents/G-ide/wecom-bot/main.py'
    
    if not backup_file(filepath):
        print(f"文件不存在: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并替换报表生成调用
    old_pattern = r"return ReportGenerator\.generate_report\(report_data, report_date, total_operations, zip_filename, self\.file_dir, 'both'\)"
    
    new_code = """# 获取月累计数据
                    monthly_data = None
                    if hasattr(self, 'db') and self.db and report_date:
                        try:
                            year_month = report_date.strftime('%Y-%m')
                            monthly_summary = self.db.get_monthly_summary(year_month)
                            # 转换为字典格式 {account: total_count}
                            monthly_data = {item['account']: item['total_count'] for item in monthly_summary}
                        except Exception as e:
                            logging.error(f"获取月累计数据失败: {e}")
                            
                    return ReportGenerator.generate_report(report_data, report_date, total_operations, zip_filename, self.file_dir, 'both', monthly_data)"""
    
    content = re.sub(old_pattern, new_code, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"已修复: {filepath}")
    return True

def fix_web_server_py():
    """修复 web_server.py"""
    filepath = 'd:/Documents/G-ide/wecom-bot/web_server.py'
    
    if not backup_file(filepath):
        print(f"文件不存在: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并替换报表生成调用
    old_pattern = r"# 生成报表\s+from report_generator import ReportGenerator\s+result = ReportGenerator\.generate_report\(\s+report_data, target_date, total_operations,\s+f\"manual_{date_str}\.zip\", app\.config\['UPLOAD_FOLDER'\], 'both'\s+\)"
    
    new_code = """# 获取月累计数据
        monthly_data = None
        try:
            year_month = target_date.strftime('%Y-%m')
            monthly_summary = db.get_monthly_summary(year_month)
            monthly_data = {item['account']: item['total_count'] for item in monthly_summary}
        except Exception as e:
            logging.error(f"获取月累计数据失败: {e}")
        
        # 生成报表
        from report_generator import ReportGenerator
        result = ReportGenerator.generate_report(
            report_data, target_date, total_operations,
            f"manual_{date_str}.zip", app.config['UPLOAD_FOLDER'], 'both', monthly_data
        )"""
    
    content = re.sub(old_pattern, new_code, content, flags=re.MULTILINE | re.DOTALL)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"已修复: {filepath}")
    return True

def fix_report_generator_py():
    """修复 report_generator.py"""
    filepath = 'd:/Documents/G-ide/wecom-bot/report_generator.py'
    
    if not backup_file(filepath):
        print(f"文件不存在: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 修改函数签名
    for i, line in enumerate(lines):
        if 'def generate_report(report_data, report_date, total_operations, filename, file_dir, output_format=' in line:
            lines[i] = line.replace("output_format='both'):", "output_format='both', monthly_data=None):")
            break
    
    # 修改数据处理逻辑 - 添加月累计数据
    for i, line in enumerate(lines):
        if "'count': member['count']" in line and "'monthly_count'" not in line:
            indent = len(line) - len(line.lstrip())
            lines.insert(i+1, ' ' * (indent+4) + "# 获取月累计数据\n")
            lines.insert(i+2, ' ' * (indent+4) + "monthly_count = 0\n")
            lines.insert(i+3, ' ' * (indent+4) + "if monthly_data and member['account'] in monthly_data:\n")
            lines.insert(i+4, ' ' * (indent+8) + "monthly_count = monthly_data[member['account']]\n")
            lines.insert(i+5, ' ' * (indent+4) + "\n")
            # 修改 append 行
            for j in range(i+6, min(i+15, len(lines))):
                if "all_members.append({" in lines[j]:
                    # 找到对应的 }) 行
                    for k in range(j, min(j+10, len(lines))):
                        if "})" in lines[k]:
                            lines[k] = lines[k].replace("})", ",\n" + ' ' * (indent+8) + "'monthly_count': monthly_count\n" + ' ' * (indent+4) + "})")
                            break
                    break
            break
    
    # 修改表格头
    for i, line in enumerate(lines):
        if 'table_lines.append("| 排名 | 团队 | 姓名 | 账号 | 听录音次数 |")' in line:
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + "# 添加表格头（包含月累计列）\n"
            lines.insert(i+1, ' ' * indent + "if monthly_data:\n")
            lines.insert(i+2, ' ' * (indent+4) + 'table_lines.append("| 排名 | 团队 | 姓名 | 账号 | 当日次数 | 月累计 |")\n')
            lines.insert(i+3, ' ' * indent + "else:\n")
            lines.insert(i+4, ' ' * (indent+4) + 'table_lines.append("| 排名 | 团队 | 姓名 | 账号 | 听录音次数 |")\n')
            break
    
    # 修改表格数据行
    for i, line in enumerate(lines):
        if 'table_lines.append(f"| {i} | {member' in line and '| {member[\'count\']} |")' in line:
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + "# 添加表格数据\n"
            lines.insert(i+1, ' ' * indent + "for i, member in enumerate(all_members_sorted, start=1):\n")
            lines.insert(i+2, ' ' * (indent+4) + "if monthly_data:\n")
            lines.insert(i+3, ' ' * (indent+8) + 'table_lines.append(f"| {i} | {member[\'team\']} | {member[\'name\']} | {member[\'account\']} | {member[\'count\']} | {member[\'monthly_count\']} |")\n')
            lines.insert(i+4, ' ' * (indent+4) + "else:\n")
            lines.insert(i+5, ' ' * (indent+8) + 'table_lines.append(f"| {i} | {member[\'team\']} | {member[\'name\']} | {member[\'account\']} | {member[\'count\']} |")\n')
            # 删除原来的循环
            if i+6 < len(lines) and 'for i, member in enumerate' in lines[i+6]:
                del lines[i+6]
            break
    
    # 修改图片生成调用
    for i, line in enumerate(lines):
        if 'ReportGenerator._generate_image_report(full_image_lines, image_path)' in line:
            lines[i] = line.replace('image_path)', 'image_path, has_monthly=bool(monthly_data))')
            break
    
    # 修改 _generate_image_report 函数签名
    for i, line in enumerate(lines):
        if 'def _generate_image_report(report_lines, output_path):' in line:
            lines[i] = line.replace('output_path):', 'output_path, has_monthly=False):')
            break
    
    # 修改表格列宽设置
    for i, line in enumerate(lines):
        if "col_widths = [0.1, 0.15, 0.25, 0.2, 0.3]  # 排名、团队、姓名、账号、操作次数" in line:
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + "if has_monthly:\n"
            lines.insert(i+1, ' ' * (indent+4) + "col_widths = [0.08, 0.12, 0.2, 0.18, 0.2, 0.22]  # 排名、团队、姓名、账号、当日次数、月累计\n")
            lines.insert(i+2, ' ' * indent + "else:\n")
            lines.insert(i+3, ' ' * (indent+4) + "col_widths = [0.1, 0.15, 0.25, 0.2, 0.3]  # 排名、团队、姓名、账号、操作次数\n")
            break
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"已修复: {filepath}")
    return True

if __name__ == '__main__':
    print("开始修复...")
    print("=" * 60)
    
    success = True
    
    # 修复 main.py
    if not fix_main_py():
        success = False
    
    # 修复 web_server.py
    if not fix_web_server_py():
        success = False
    
    # 修复 report_generator.py
    if not fix_report_generator_py():
        success = False
    
    print("=" * 60)
    if success:
        print("所有文件修复完成！")
        print("\n请注意：")
        print("1. 已创建备份文件（.backup后缀）")
        print("2. 请重启web服务器以应用更改")
        print("3. 建议测试上传功能和报表生成功能")
    else:
        print("部分文件修复失败，请检查错误信息")
