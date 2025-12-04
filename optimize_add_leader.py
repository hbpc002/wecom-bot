#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
优化 add_team_leader 方法的脚本
在添加新组长时，自动更新历史数据的团队名称并重新计算月汇总
"""

import re
import shutil
from datetime import datetime

def optimize_add_team_leader():
    """优化 add_team_leader 方法"""
    filepath = 'database.py'
    
    # 备份文件
    backup_path = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"✓ 已备份文件到: {backup_path}")
    
    # 读取文件
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到需要修改的 add_team_leader 方法
    old_pattern = r'''    def add_team_leader\(self, team_name: str, account_id: str, name: str\) -> bool:
        \"\"\"添加团队组长映射
        
        Args:
            team_name: 团队名称
            account_id: 账号ID
            name: 姓名
            
        Returns:
            bool: 是否添加成功
        \"\"\"
        try:
            cursor = self\.conn\.cursor\(\)
            cursor\.execute\(\'\'\'
                INSERT INTO team_leaders \(team_name, account_id, name\)
                VALUES \(\?, \?, \?\)
            \'\'\', \(team_name, account_id, name\)\)
            
            self\.conn\.commit\(\)
            logging\.info\(f\"添加团队组长成功: \{team_name\} - \{name\} \(\{account_id\}\)\"\)
            return True
            
        except Exception as e:
            logging\.error\(f\"添加团队组长失败: \{e\}\"\)
            self\.conn\.rollback\(\)
            return False'''
    
    # 新的优化方法
    new_code = '''    def add_team_leader(self, team_name: str, account_id: str, name: str) -> bool:
        """添加团队组长映射
        
        Args:
            team_name: 团队名称
            account_id: 账号ID
            name: 姓名
            
        Returns:
            bool: 是否添加成功
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(\'\'\'
                INSERT INTO team_leaders (team_name, account_id, name)
                VALUES (?, ?, ?)
            \'\'\', (team_name, account_id, name))
            
            # 更新历史数据中该账号的团队名称和姓名
            cursor.execute(\'\'\'
                UPDATE daily_summary
                SET team = ?, name = ?
                WHERE account = ?
            \'\'\', (team_name, name, account_id))
            daily_updated = cursor.rowcount
            
            cursor.execute(\'\'\'
                UPDATE listening_records
                SET team = ?, name = ?
                WHERE account = ?
            \'\'\', (team_name, name, account_id))
            records_updated = cursor.rowcount
            
            # 获取该账号的所有相关年月，重新计算月汇总
            cursor.execute(\'\'\'
                SELECT DISTINCT strftime('%Y-%m', date) as year_month
                FROM daily_summary
                WHERE account = ?
            \'\'\', (account_id,))
            
            year_months = [row[0] for row in cursor.fetchall()]
            
            # 重新计算影响的月份的月汇总
            for year_month in year_months:
                if year_month:  # 确保不是空值
                    cursor.execute('DELETE FROM monthly_summary WHERE year_month = ? AND account = ?', 
                                 (year_month, account_id))
                    
                    cursor.execute(\'\'\'
                        INSERT INTO monthly_summary (year_month, account, name, team, total_count, updated_at)
                        SELECT ?, account, ?, ?, SUM(count) as total_count, CURRENT_TIMESTAMP
                        FROM daily_summary
                        WHERE account = ? AND strftime('%Y-%m', date) = ?
                        GROUP BY account
                    \'\'\', (year_month, name, team_name, account_id, year_month))
            
            self.conn.commit()
            logging.info(f"添加团队组长成功: {team_name} - {name} ({account_id})")
            if daily_updated > 0 or records_updated > 0:
                logging.info(f"已更新历史数据: daily_summary={daily_updated}条, listening_records={records_updated}条, 月汇总={len(year_months)}个月")
            return True
            
        except Exception as e:
            logging.error(f"添加团队组长失败: {e}")
            self.conn.rollback()
            return False'''
    
    # 执行替换
    new_content = re.sub(old_pattern, new_code, content, flags=re.MULTILINE)
    
    if new_content == content:
        print("⚠ 警告: 未找到匹配的代码块，可能文件已被修改")
        return False
    
    # 写入修改后的内容
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✓ 已成功修改 {filepath}")
    print("\n优化说明:")
    print("1. 添加新组长时，自动更新该账号在 daily_summary 和 listening_records 中的团队名称和姓名")
    print("2. 自动重新计算该账号相关月份的月汇总数据")
    print("3. 这样以后新增组长时，月累计数据会自动更新，无需手动运行修复脚本")
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("优化 add_team_leader 方法脚本")
    print("=" * 60)
    
    try:
        success = optimize_add_team_leader()
        
        if success:
            print("\n" + "=" * 60)
            print("✓ 优化完成！")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("✗ 优化失败")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
