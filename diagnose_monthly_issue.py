#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
诊断月累计数据问题
检查数据库表中的数据，找出月累计为0的原因
"""

import sqlite3
import os
from datetime import datetime, date

def diagnose_monthly_issue():
    """诊断月累计问题"""
    db_path = 'data/wecom_bot.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    print("=" * 60)
    print("诊断月累计数据问题")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. 检查 team_leaders 表
    print("\n1. 检查 team_leaders 表:")
    cursor.execute("SELECT * FROM team_leaders ORDER BY team_name, name")
    leaders = cursor.fetchall()
    print(f"   组长总数: {len(leaders)}")
    for leader in leaders:
        print(f"   - {leader['team_name']}: {leader['name']} ({leader['account_id']})")
    
    # 2. 检查 daily_summary 表（最近的数据）
    print("\n2. 检查 daily_summary 表（最近3天）:")
    cursor.execute("""
        SELECT date, account, name, team, count 
        FROM daily_summary 
        ORDER BY date DESC 
        LIMIT 20
    """)
    daily_records = cursor.fetchall()
    print(f"   最近记录数: {len(daily_records)}")
    for record in daily_records:
        print(f"   - {record['date']}: {record['team']} - {record['name']} ({record['account']}) = {record['count']}")
    
    # 3. 检查 monthly_summary 表
    print("\n3. 检查 monthly_summary 表:")
    cursor.execute("""
        SELECT year_month, account, name, team, total_count 
        FROM monthly_summary 
        ORDER BY year_month DESC, total_count DESC
    """)
    monthly_records = cursor.fetchall()
    print(f"   月汇总记录数: {len(monthly_records)}")
    for record in monthly_records:
        print(f"   - {record['year_month']}: {record['team']} - {record['name']} ({record['account']}) = {record['total_count']}")
    
    # 4. 检查是否有账号在 daily_summary 中但不在 monthly_summary 中
    print("\n4. 检查数据不一致的账号:")
    today = date.today()
    year_month = today.strftime('%Y-%m')
    
    cursor.execute("""
        SELECT DISTINCT d.account, d.name, d.team
        FROM daily_summary d
        LEFT JOIN monthly_summary m ON d.account = m.account AND m.year_month = ?
        WHERE strftime('%Y-%m', d.date) = ?
        AND m.account IS NULL
    """, (year_month, year_month))
    
    missing_accounts = cursor.fetchall()
    if missing_accounts:
        print(f"   ⚠ 发现 {len(missing_accounts)} 个账号在 daily_summary 中有数据，但 monthly_summary 中没有:")
        for account in missing_accounts:
            print(f"   - {account['team']} - {account['name']} ({account['account']})")
    else:
        print("   ✓ 所有账号数据一致")
    
    # 5. 检查团队名称不一致的情况
    print("\n5. 检查团队名称不一致:")
    cursor.execute("""
        SELECT d.account, d.name, d.team as daily_team, t.team_name as leader_team
        FROM daily_summary d
        INNER JOIN team_leaders t ON d.account = t.account_id
        WHERE d.team != t.team_name
        LIMIT 10
    """)
    
    inconsistent_teams = cursor.fetchall()
    if inconsistent_teams:
        print(f"   ⚠ 发现 {len(inconsistent_teams)} 条记录的团队名称不一致:")
        for record in inconsistent_teams:
            print(f"   - {record['name']} ({record['account']}): daily='{record['daily_team']}' vs leader='{record['leader_team']}'")
    else:
        print("   ✓ 所有团队名称一致")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)

if __name__ == '__main__':
    diagnose_monthly_issue()
