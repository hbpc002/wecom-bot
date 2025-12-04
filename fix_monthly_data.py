#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复月累计问题
1. 更新 daily_summary 中的团队名称，使其与 team_leaders 表一致
2. 重新计算月汇总数据
"""

import sqlite3
import os
from datetime import datetime

def fix_monthly_issue():
    """修复月累计问题"""
    db_path = 'data/wecom_bot.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    print("=" * 60)
    print("修复月累计数据问题")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. 更新 daily_summary 中的团队名称和姓名，使其与 team_leaders 一致
        print("\n1. 更新 daily_summary 中的团队名称和姓名...")
        cursor.execute("""
            UPDATE daily_summary
            SET team = (SELECT team_name FROM team_leaders WHERE account_id = daily_summary.account),
                name = (SELECT name FROM team_leaders WHERE account_id = daily_summary.account)
            WHERE account IN (SELECT account_id FROM team_leaders)
        """)
        
        updated_count = cursor.rowcount
        print(f"   ✓ 已更新 {updated_count} 条记录")
        
        # 2. 同样更新 listening_records 中的团队名称和姓名
        print("\n2. 更新 listening_records 中的团队名称和姓名...")
        cursor.execute("""
            UPDATE listening_records
            SET team = (SELECT team_name FROM team_leaders WHERE account_id = listening_records.account),
                name = (SELECT name FROM team_leaders WHERE account_id = listening_records.account)
            WHERE account IN (SELECT account_id FROM team_leaders)
        """)
        
        updated_count = cursor.rowcount
        print(f"   ✓ 已更新 {updated_count} 条记录")
        
        # 3. 获取所有需要更新的年月
        print("\n3. 获取需要重新计算的年月...")
        cursor.execute("""
            SELECT DISTINCT strftime('%Y-%m', date) as year_month
            FROM daily_summary
            ORDER BY year_month DESC
        """)
        
        year_months = [row[0] for row in cursor.fetchall()]
        print(f"   找到 {len(year_months)} 个月份需要更新: {year_months}")
        
        # 4. 重新计算每个月的月汇总
        print("\n4. 重新计算月汇总数据...")
        for year_month in year_months:
            # 删除旧数据
            cursor.execute('DELETE FROM monthly_summary WHERE year_month = ?', (year_month,))
            
            # 重新计算
            cursor.execute('''
                INSERT INTO monthly_summary (year_month, account, name, team, total_count, updated_at)
                SELECT ?, account, name, team, SUM(count) as total_count, CURRENT_TIMESTAMP
                FROM daily_summary
                WHERE strftime('%Y-%m', date) = ?
                GROUP BY account, name, team
            ''', (year_month, year_month))
            
            inserted_count = cursor.rowcount
            print(f"   ✓ {year_month}: 插入 {inserted_count} 条汇总记录")
        
        # 提交所有更改
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✓ 修复完成！")
        print("=" * 60)
        print("\n修复内容:")
        print("1. 更新了 daily_summary 和 listening_records 中的团队名称和姓名")
        print("2. 重新计算了所有月份的月汇总数据")
        print("\n建议:")
        print("1. 刷新网页查看最新数据")
        print("2. 如果问题仍然存在，请再次运行诊断脚本检查")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == '__main__':
    fix_monthly_issue()
