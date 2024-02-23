import sqlite3
import subprocess
import datetime
from concurrent.futures import ThreadPoolExecutor
import re

# 数据库设置
db_file = 'balance_records.db'

# 连接数据库
conn = sqlite3.connect(db_file)
cur = conn.cursor()

# 创建表
cur.execute('''
CREATE TABLE IF NOT EXISTS balances (
    address TEXT PRIMARY KEY,
    balance INTEGER,
    date TEXT
)
''')
conn.commit()

# 读取地址
with open('bbn_addr.txt', 'r') as f:
    addresses = f.read().splitlines()

# 获取日期
current_date = datetime.datetime.now().strftime('%Y-%m-%d')
yesterday_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

# 文件名
balance_file = f"balances_record_{current_date}.txt"
yesterday_balance_file = f"balances_record_{yesterday_date}.txt"

# 清空当前余额文件
open(balance_file, 'w').close()

# 初始化变量
total_balance = 0
not_increased_lines = []
zero_balance_lines = []

def query_balance(address):
    # 执行外部命令获取余额
    result = subprocess.run(['babylond', 'query', 'bank', 'balances', address, '--log_format', 'json'], capture_output=True, text=True)
    balance_raw = re.search(r'"amount":"(\d+)"', result.stdout)
    balance = int(balance_raw.group(1)) if balance_raw else 0
    
    # 更新数据库
    cur.execute('INSERT OR REPLACE INTO balances (address, balance, date) VALUES (?, ?, ?)', (address, balance, current_date))
    conn.commit()

    # 写入文件
    with open(balance_file, 'a') as f:
        f.write(f"{address} {balance}\n")

    return address, balance

# 并发查询余额
with ThreadPoolExecutor(max_workers=2) as executor:
    for address, balance in executor.map(query_balance, addresses):
        total_balance += balance

        # 检查余额是否未增长
        cur.execute('SELECT balance FROM balances WHERE address = ? AND date = ?', (address, yesterday_date))
        prev_balance = cur.fetchone()
        if prev_balance and balance <= prev_balance[0]:
            not_increased_lines.append(addresses.index(address) + 1)

        # 检查余额是否为0
        if balance == 0:
            zero_balance_lines.append(addresses.index(address) + 1)

# 显示总余额
print(f"Total balance: {total_balance / 1000000:.2f}")

# 输出余额未发生增长的地址行号
if not_increased_lines:
    print(f"Addresses with no increase in balance: {','.join(map(str, not_increased_lines))}")

# 输出余额为0的地址行号
if zero_balance_lines:
    print(f"Zero balance lines: {','.join(map(str, zero_balance_lines))}")

# 关闭数据库连接
conn.close()
