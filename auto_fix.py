#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动修复脚本：为报表添加月累计列功能
"""

import re

def fix_report_generator():
    """修复 report_generator.py"""
    filepath = 'd:/Documents/G-ide/wecom-bot/report_generator.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修改1: 函数签名
    content = content.replace(
        "def generate_report(report_data, report_date, total_operations, filename, file_dir, output_format='both'):",
        "def generate_report(report_data, report_date, total_operations, filename, file_dir, output_format='both', monthly_data=None):"
    )
    
    # 修改2: 数据处理逻辑
    old_members_code = """        # 新增代码：将所有团队成员数据合并到一个列表中
        all_members = []
        for team, members in team_data.items():
            for member in members:
                all_members.append({
                    'team': team,
                    'name': member['name'],
                    'account': member['account'],
                    'count': member['count']
                })"""
    
    new_members_code = """        # 新增代码：将所有团队成员数据合并到一个列表中
        all_members = []
        for team, members in team_data.items():
            for member in members:
                # 获取月累计数据
                monthly_count = 0
                if monthly_data and member['account'] in monthly_data:
                    monthly_count = monthly_data[member['account']]
                
                all_members.append({
                    'team': team,
                    'name': member['name'],
                    'account': member['account'],
                    'count': member['count'],
                    'monthly_count': monthly_count
                })"""
    
    content = content.replace(old_members_code, new_members_code)
    
    # 修改3: 表格头
    old_header = '        # 添加表格头\n        table_lines.append("| 排名 | 团队 | 姓名 | 账号 | 听录音次数 |")'
    new_header = '''        # 添加表格头（包含月累计列）
        if monthly_data:
            table_lines.append("| 排名 | 团队 | 姓名 | 账号 | 当日次数 | 月累计 |")
        else:
            table_lines.append("| 排名 | 团队 | 姓名 | 账号 | 听录音次数 |")'''
    
    content = content.replace(old_header, new_header)
    
    # 修改4: 表格数据行
    old_data_rows = '''        # 添加表格数据
        for i, member in enumerate(all_members_sorted, start=1):
            table_lines.append(f"| {i} | {member['team']} | {member['name']} | {member['account']} | {member['count']} |")'''
    
    new_data_rows = '''        # 添加表格数据
        for i, member in enumerate(all_members_sorted, start=1):
            if monthly_data:
                table_lines.append(f"| {i} | {member['team']} | {member['name']} | {member['account']} | {member['count']} | {member['monthly_count']} |")
            else:
                table_lines.append(f"| {i} | {member['team']} | {member['name']} | {member['account']} | {member['count']} |")'''
    
    content = content.replace(old_data_rows, new_data_rows)
    
    # 修改5: 图片生成调用
    content = content.replace(
        "ReportGenerator._generate_image_report(full_image_lines, image_path)",
        "ReportGenerator._generate_image_report(full_image_lines, image_path, has_monthly=bool(monthly_data))"
    )
    
    # 修改6: _generate_image_report 函数签名
    content = content.replace(
        "def _generate_image_report(report_lines, output_path):",
        "def _generate_image_report(report_lines, output_path, has_monthly=False):"
    )
    
    # 修改7: 表格列宽设置（两处）
    old_col_widths = "                col_widths = [0.1, 0.15, 0.25, 0.2, 0.3]  # 排名、团队、姓名、账号、操作次数"
    new_col_widths = """                if has_monthly:
                    col_widths = [0.08, 0.12, 0.2, 0.18, 0.2, 0.22]  # 排名、团队、姓名、账号、当日次数、月累计
                else:
                    col_widths = [0.1, 0.15, 0.25, 0.2, 0.3]  # 排名、团队、姓名、账号、操作次数"""
    
    content = content.replace(old_col_widths, new_col_widths)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已修复: {filepath}")
    return True

def fix_web_server():
    """修复 web_server.py"""
    filepath = 'd:/Documents/G-ide/wecom-bot/web_server.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找 send_to_wecom 函数中的报表生成部分
    old_code = '''        # 生成报表
        from report_generator import ReportGenerator
        result = ReportGenerator.generate_report(
            report_data, target_date, total_operations,
            f"manual_{date_str}.zip", app.config['UPLOAD_FOLDER'], 'both'
        )'''
    
    new_code = '''        # 获取月累计数据
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
        )'''
    
    content = content.replace(old_code, new_code)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已修复: {filepath}")
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("开始自动修复...")
    print("=" * 60)
    
    try:
        # 修复 report_generator.py
        if fix_report_generator():
            print("✅ report_generator.py 修复成功")
        else:
            print("❌ report_generator.py 修复失败")
        
        # 修复 web_server.py
        if fix_web_server():
            print("✅ web_server.py 修复成功")
        else:
            print("❌ web_server.py 修复失败")
        
        print("=" * 60)
        print("✅ 所有修复完成！")
        print("\n下一步:")
        print("1. 重启 web_server.py")
        print("2. 测试上传功能")
        print("3. 测试报表生成功能")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 修复过程中出错: {e}")
        import traceback
        traceback.print_exc()
