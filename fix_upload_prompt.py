#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复上传提示与报表查询数据不一致的问题

问题：上传提示使用 report_data 统计（只计算 team_mapping 中的组长）
     而报表查询使用数据库（INNER JOIN team_leaders）
     
解决：修改 process_zip_file 方法，改为从数据库查询当日汇总数据来生成上传提示
"""

import re
import shutil
from datetime import datetime

def fix_main_py():
    """修改 main.py 中的 process_zip_file 方法"""
    
    file_path = 'main.py'
    backup_path = f'main.py.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    # 备份原文件
    shutil.copy2(file_path, backup_path)
    print(f"已备份原文件到: {backup_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到需要修改的部分：在保存数据库之后，返回报表之前
    # 我们需要在第 234-249 行的数据库保存逻辑之后添加代码
    
    old_code = """                    # 如果有数据库连接，保存数据到数据库
                    if hasattr(self, 'db') and self.db and records_to_insert:
                        try:
                            logging.info(f"正在保存 {len(records_to_insert)} 条记录到数据库...")
                            self.db.insert_batch_records(records_to_insert)
                            
                            if report_date:
                                logging.info(f"正在更新日汇总: {report_date}")
                                self.db.update_daily_summary(report_date)
                                
                                year_month = report_date.strftime('%Y-%m')
                                logging.info(f"正在更新月汇总: {year_month}")
                                self.db.update_monthly_summary(year_month)
                        except Exception as e:
                            logging.error(f"保存数据到数据库失败: {e}")

                    return ReportGenerator.generate_report(report_data, report_date, total_operations, zip_filename, self.file_dir, 'both')"""
    
    new_code = """                    # 如果有数据库连接，保存数据到数据库
                    if hasattr(self, 'db') and self.db and records_to_insert:
                        try:
                            logging.info(f"正在保存 {len(records_to_insert)} 条记录到数据库...")
                            self.db.insert_batch_records(records_to_insert)
                            
                            if report_date:
                                logging.info(f"正在更新日汇总: {report_date}")
                                self.db.update_daily_summary(report_date)
                                
                                year_month = report_date.strftime('%Y-%m')
                                logging.info(f"正在更新月汇总: {year_month}")
                                self.db.update_monthly_summary(year_month)
                                
                                # 从数据库查询当日汇总数据，确保上传提示与报表查询一致
                                try:
                                    daily_summary = self.db.get_daily_summary(report_date)
                                    
                                    # 重新计算统计数据（基于数据库查询结果）
                                    db_total_operations = sum(item['count'] for item in daily_summary)
                                    db_people_count = len(daily_summary)
                                    
                                    # 重新构建 report_data（基于数据库查询结果）
                                    db_report_data = {}
                                    for item in daily_summary:
                                        key = (item['team'], item['name'], item['account'])
                                        db_report_data[key] = item['count']
                                    
                                    logging.info(f"数据库查询结果: 总次数={db_total_operations}, 参与人数={db_people_count}")
                                    
                                    # 使用数据库查询的结果生成报表
                                    return ReportGenerator.generate_report(
                                        db_report_data, 
                                        report_date, 
                                        db_total_operations, 
                                        zip_filename, 
                                        self.file_dir, 
                                        'both'
                                    )
                                except Exception as e:
                                    logging.error(f"从数据库查询汇总数据失败，使用原始统计: {e}")
                                    # 如果数据库查询失败，回退到原始逻辑
                                    return ReportGenerator.generate_report(report_data, report_date, total_operations, zip_filename, self.file_dir, 'both')
                        except Exception as e:
                            logging.error(f"保存数据到数据库失败: {e}")

                    # 如果没有数据库连接或保存失败，使用原始统计
                    return ReportGenerator.generate_report(report_data, report_date, total_operations, zip_filename, self.file_dir, 'both')"""
    
    # 执行替换
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("✓ 已找到并替换 process_zip_file 方法中的代码")
    else:
        print("✗ 未找到目标代码，请检查文件内容")
        return False
    
    # 写入修改后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ 已成功修改 {file_path}")
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("开始修复上传提示与报表查询数据不一致问题...")
    print("=" * 60)
    
    success = fix_main_py()
    
    if success:
        print("\n" + "=" * 60)
        print("修复完成！")
        print("=" * 60)
        print("\n修改内容：")
        print("- 在保存数据库并更新汇总后，从数据库查询当日汇总数据")
        print("- 使用数据库查询结果重新计算统计信息（总次数、参与人数）")
        print("- 确保上传提示与报表查询显示相同的数据")
        print("\n建议：")
        print("1. 重启 web_server.py 使修改生效")
        print("2. 上传一个测试文件验证修复效果")
    else:
        print("\n修复失败，请手动检查代码")
