import sqlite3
from datetime import datetime

# 连接数据库
conn = sqlite3.connect('data/wecom_bot.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 50)
print("检查 2025-10-31 的数据")
print("=" * 50)

target_date = '2025-10-31'

# 1. 检查原始记录表
print("\n1. 原始记录表 (listening_records):")
cursor.execute('''
    SELECT date, account, name, team, COUNT(*) as count
    FROM listening_records
    WHERE date = ?
    GROUP BY account, name, team
    ORDER BY count DESC
''', (target_date,))

records = cursor.fetchall()
if records:
    print(f"找到 {len(records)} 条记录")
    for row in records:
        print(f"  账号: {row['account']}, 姓名: {row['name']}, 团队: {row['team']}, 次数: {row['count']}")
    total = sum(row['count'] for row in records)
    print(f"总次数: {total}")
else:
    print("未找到记录")

# 2. 检查日汇总表
print("\n2. 日汇总表 (daily_summary):")
cursor.execute('''
    SELECT date, account, name, team, count
    FROM daily_summary
    WHERE date = ?
    ORDER BY count DESC
''', (target_date,))

summary = cursor.fetchall()
if summary:
    print(f"找到 {len(summary)} 条汇总")
    for row in summary:
        print(f"  账号: {row['account']}, 姓名: {row['name']}, 团队: {row['team']}, 次数: {row['count']}")
    total = sum(row['count'] for row in summary)
    print(f"总次数: {total}")
else:
    print("未找到汇总")

# 3. 检查团队组长表
print("\n3. 团队组长表 (team_leaders):")
cursor.execute('SELECT id, team_name, account_id, name FROM team_leaders ORDER BY id')
leaders = cursor.fetchall()
if leaders:
    print(f"找到 {len(leaders)} 个组长")
    for row in leaders:
        print(f"  ID: {row['id']}, 团队: {row['team_name']}, 账号: {row['account_id']}, 姓名: {row['name']}")
else:
    print("未找到组长")

# 4. 检查 INNER JOIN 查询结果（模拟 get_daily_with_monthly）
print("\n4. INNER JOIN 查询结果（模拟 get_daily_with_monthly）:")
cursor.execute('''
    SELECT 
        t.account_id as account, 
        t.name, 
        t.team_name as team, 
        d.count as daily_count
    FROM daily_summary d
    INNER JOIN team_leaders t ON d.account = t.account_id
    WHERE d.date = ?
    ORDER BY d.count DESC
''', (target_date,))

join_results = cursor.fetchall()
if join_results:
    print(f"找到 {len(join_results)} 条匹配记录")
    for row in join_results:
        print(f"  账号: {row['account']}, 姓名: {row['name']}, 团队: {row['team']}, 次数: {row['daily_count']}")
    total = sum(row['daily_count'] for row in join_results)
    print(f"总次数: {total}")
else:
    print("未找到匹配记录（这就是问题所在！）")

# 5. 找出在 daily_summary 但不在 team_leaders 的账号
print("\n5. 在 daily_summary 但不在 team_leaders 的账号:")
cursor.execute('''
    SELECT DISTINCT d.account, d.name, d.team
    FROM daily_summary d
    LEFT JOIN team_leaders t ON d.account = t.account_id
    WHERE d.date = ? AND t.account_id IS NULL
''', (target_date,))

missing = cursor.fetchall()
if missing:
    print(f"找到 {len(missing)} 个未匹配账号")
    for row in missing:
        print(f"  账号: {row['account']}, 姓名: {row['name']}, 团队: {row['team']}")
else:
    print("所有账号都在 team_leaders 表中")

conn.close()
print("\n" + "=" * 50)
