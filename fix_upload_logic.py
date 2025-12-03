#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
优化上传逻辑修改脚本
自动修改 main.py，使其保存所有CSV数据到数据库，非组长账号标记为"未分配组"
"""

import re
import shutil
import os
from datetime import datetime

def backup_file(filepath):
    """备份文件"""
    backup_path = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"✓ 已备份文件到: {backup_path}")
    return backup_path

def modify_main_py():
    """修改 main.py 的 process_zip_file 方法"""
    filepath = 'main.py'
    
    # 备份文件
    backup_file(filepath)
    
    # 读取文件
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到需要修改的代码块（第183-220行左右）
    # 原来的逻辑：只处理 team_mapping 中的账号
    old_pattern = r'''                    for row_num, row in enumerate\(reader, start=2\):  # 从第2行开始计数
                        try:
                            if len\(row\) < 6:  # 确保有足够的列
                                continue
                                
                            account = row\[1\]\.strip\(\)  # 帐号在第2列
                            name = row\[2\]\.strip\(\)     # 姓名在第3列
                            operation_time = row\[5\]\.strip\(\)  # 操作时间在第6列
                            
                            # 跳过空行
                            if not account or not name:
                                continue
                                
                            logging\.debug\(f"处理数据: 账号={account}, 姓名={name}, 时间={operation_time}"\)
                            
                            # 如果账号在团队映射中，则统计
                            if account in self\.team_mapping:
                                team = self\.team_mapping\[account\]
                                key = \(team, name, account\)
                                if key not in report_data:
                                    report_data\[key\] = 0
                                report_data\[key\] \+= 1
                                total_operations \+= 1
                                
                                # 收集操作时间
                                if operation_time:
                                    operation_dates\.append\(operation_time\)
                                    records_to_insert\.append\(\{
                                        'account': account,
                                        'name': name,
                                        'team': team,
                                        'operation_time': operation_time,
                                        'source_file': zip_filename
                                    \}\)
                                
                        except Exception as e:
                            logging\.warning\(f"跳过第\{row_num\}行数据: \{e\}, 行内容: \{row\}"\)
                            continue'''
    
    # 新的逻辑：保存所有数据，非组长标记为"未分配组"
    new_code = '''                    for row_num, row in enumerate(reader, start=2):  # 从第2行开始计数
                        try:
                            if len(row) < 6:  # 确保有足够的列
                                continue
                                
                            account = row[1].strip()  # 帐号在第2列
                            name = row[2].strip()     # 姓名在第3列
                            operation_time = row[5].strip()  # 操作时间在第6列
                            
                            # 跳过空行
                            if not account or not name:
                                continue
                                
                            logging.debug(f"处理数据: 账号={account}, 姓名={name}, 时间={operation_time}")
                            
                            # 确定团队名称：如果在映射中则使用映射的团队，否则标记为"未分配组"
                            if account in self.team_mapping:
                                team = self.team_mapping[account]
                            else:
                                team = "未分配组"
                            
                            # 收集操作时间和数据库记录（所有记录都保存）
                            if operation_time:
                                operation_dates.append(operation_time)
                                records_to_insert.append({
                                    'account': account,
                                    'name': name,
                                    'team': team,
                                    'operation_time': operation_time,
                                    'source_file': zip_filename
                                })
                            
                            # 只有组长的数据才统计到 report_data（用于即时报表生成）
                            if account in self.team_mapping:
                                key = (team, name, account)
                                if key not in report_data:
                                    report_data[key] = 0
                                report_data[key] += 1
                                total_operations += 1
                                
                        except Exception as e:
                            logging.warning(f"跳过第{row_num}行数据: {e}, 行内容: {row}")
                            continue'''
    
    # 执行替换
    new_content = re.sub(old_pattern, new_code, content, flags=re.MULTILINE)
    
    if new_content == content:
        print("⚠ 警告: 未找到匹配的代码块，可能文件已被修改")
        return False
    
    # 写入修改后的内容
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✓ 已成功修改 {filepath}")
    print("\n修改说明:")
    print("1. 现在会保存所有CSV数据到数据库")
    print("2. 非组长账号标记为'未分配组'")
    print("3. report_data 仍然只包含组长数据（用于即时报表生成）")
    print("4. 数据库查询逻辑无需修改，已经使用 INNER JOIN 筛选组长")
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("优化上传逻辑修改脚本")
    print("=" * 60)
    
    try:
        success = modify_main_py()
        
        if success:
            print("\n" + "=" * 60)
            print("✓ 修改完成！")
            print("=" * 60)
            print("\n下一步:")
            print("1. 重启 web_server.py 以应用更改")
            print("2. 上传测试文件验证功能")
        else:
            print("\n" + "=" * 60)
            print("✗ 修改失败，请检查代码")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
