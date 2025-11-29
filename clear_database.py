import sqlite3, traceback, os

db_file = 'data/wecom_bot.db'  # 绝对路径
conn = sqlite3.connect(db_file)
conn.set_trace_callback(print)          # 可选：看实际执行的 SQL
cur = conn.cursor()

try:
    cur.execute("SELECT type, name FROM sqlite_master WHERE type='table';")
    tables = [row[1] for row in cur.fetchall()]
    print('待清空表：', tables)

    for tbl in tables:
        sql = f'DELETE FROM "{tbl}";'
        cur.execute(sql)
        print(f'{tbl}：{cur.rowcount} 行被删除')

    conn.commit()
    print('=== 已提交，数据清空完成 ===')
except Exception as e:
    traceback.print_exc()
    conn.rollback()
finally:
    conn.close()