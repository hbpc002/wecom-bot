import sqlite3
from datetime import datetime

# 连接数据库
conn = sqlite3.connect('data/wecom_bot.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 60)
print("检查 2025-12-03 的数据")
print("=" * 60)

target_date = '2025-12-03'
year_month = '2025-12'

# 1. 检查日汇总表中12月3日的数据
print("\n1. 日汇总表 (daily_summary) - 2025-12-03:")
cursor.execute('''
    SELECT date, account, name, team, count
    FROM daily_summary
    WHERE date = ?
    ORDER BY count DESC
''', (target_date,))

daily_records = cursor.fetchall()
if daily_records:
    print(f"找到 {len(daily_records)} 条记录")
    for row in daily_records[:10]:  # 只显示前10条
        print(f"  账号: {row['account']}, 姓名: {row['name']}, 团队: {row['team']}, 当日次数: {row['count']}")
else:
    print("未找到记录")

# 2. 检查月汇总表中12月的数据
print(f"\n2. 月汇总表 (monthly_summary) - {year_month}:")
cursor.execute('''
    SELECT year_month, account, name, team, total_count
    FROM monthly_summary
    WHERE year_month = ?
    ORDER BY total_count DESC
''', (year_month,))

monthly_records = cursor.fetchall()
if monthly_records:
    print(f"找到 {len(monthly_records)} 条记录")
    for row in monthly_records[:10]:  # 只显示前10条
        print(f"  账号: {row['account']}, 姓名: {row['name']}, 团队: {row['team']}, 月累计: {row['total_count']}")
else:
    print("未找到记录")

# 3. 查找当日36次的组长
print(f"\n3. 查找12月3日数据为36的组长:")
cursor.execute('''
    SELECT date, account, name, team, count
    FROM daily_summary
    WHERE date = ? AND count = 36
''', (target_date,))

target_records = cursor.fetchall()
if target_records:
    print(f"找到 {len(target_records)} 条记录")
    for row in target_records:
        print(f"  账号: {row['account']}, 姓名: {row['name']}, 团队: {row['team']}, 当日次数: {row['count']}")
        
        # 查询此账号的月累计数据
        cursor.execute('''
            SELECT year_month, total_count
            FROM monthly_summary
            WHERE account = ? AND year_month = ?
        ''', (row['account'], year_month))
        
        monthly = cursor.fetchone()
        if monthly:
            print(f"    -> 月累计: {monthly['total_count']}")
        else:
            print(f"    -> 月累计: 未找到数据（这就是问题！）")
            
        # 查询此账号在12月所有日期的数据
        cursor.execute('''
            SELECT date, count
            FROM daily_summary
            WHERE account = ? AND strftime('%Y-%m', date) = ?
            ORDER BY date
        ''', (row['account'], year_month))
        
        all_days = cursor.fetchall()
        print(f"    -> 12月所有日期数据: {len(all_days)} 天")
        for day in all_days:
            print(f"       {day['date']}: {day['count']} 次")
        
        # 计算此账号12月应该有的月累计
        total = sum(day['count'] for day in all_days)
        print(f"    -> 计算得到的月累计应该是: {total}")

else:
    print("未找到当日36次的记录")

# 4. 模拟 get_daily_with_monthly 的SQL查询
print(f"\n4. 模拟 get_daily_with_monthly 的SQL查询 (12月3日):")
cursor.execute('''
    SELECT 
        t.account_id as account, 
        t.name, 
        t.team_name as team, 
        d.count as daily_count,
        COALESCE(m.total_count, 0) as monthly_count
    FROM daily_summary d
    INNER JOIN team_leaders t ON d.account = t.account_id
    LEFT JOIN monthly_summary m 
        ON d.account = m.account AND m.year_month = ?
    WHERE d.date = ?
    ORDER BY d.count DESC
''', (year_month, target_date))

join_results = cursor.fetchall()
if join_results:
    print(f"找到 {len(join_results)} 条匹配记录")
    for row in join_results[:10]:
        print(f"  账号: {row['account']}, 姓名: {row['name']}, 团队: {row['team']}, 当日: {row['daily_count']}, 月累计: {row['monthly_count']}")
else:
    print("未找到匹配记录")

conn.close()
print("\n" + "=" * 60)
