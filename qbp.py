import sqlite3
import subprocess
import datetime
import re
from concurrent.futures import ThreadPoolExecutor

# 数据库文件路径
db_file = 'balance_records.db'

# 初始化数据库
def init_db():
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS balances (
        address TEXT PRIMARY KEY,
        balance INTEGER,
        date TEXT
    )''')
    conn.commit()
    conn.close()

# 读取地址列表
with open('bbn_addr.txt', 'r') as f:
    addresses = f.read().splitlines()

# 获取当前和昨天的日期
current_date = datetime.datetime.now().strftime('%Y-%m-%d')
yesterday_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

# 文件名
balance_file = f"balances_record_{current_date}.txt"
yesterday_balance_file = f"balances_record_{yesterday_date}.txt"

# 清空当前余额文件
open(balance_file, 'w').close()

# 初始化总余额和行号记录
total_balance = 0
not_increased_lines = []
zero_balance_lines = []

# 查询余额的函数
def query_balance(address):
    # 在每个线程内部创建数据库连接
    conn_local = sqlite3.connect(db_file)
    cur_local = conn_local.cursor()

    try:
        # 执行外部命令获取余额
        result = subprocess.run(['babylond', 'query', 'bank', 'balances', address, '--log_format', 'json'], capture_output=True, text=True)
        balance_raw = re.search(r'"amount":"(\d+)"', result.stdout)
        balance = int(balance_raw.group(1)) if balance_raw else 0
        print(f"Queried balance for {address}: {balance}")  # 实时输出
    except Exception as e:
        print(f"Error querying balance for {address}: {e}")  # 错误输出
        balance = 0

    # 更新数据库
    cur_local.execute('INSERT OR REPLACE INTO balances (address, balance, date) VALUES (?, ?, ?)', (address, balance, current_date))
    conn_local.commit()

    # 写入余额到文件
    with open(balance_file, 'a') as f:
        f.write(f"{address} {balance}\n")

    # 关闭数据库连接
    conn_local.close()

    return address, balance

# 主程序
def main():
    init_db()  # 初始化数据库

    with ThreadPoolExecutor(max_workers=2) as executor:
        # 使用线程池查询余额
        for address, balance in executor.map(query_balance, addresses):
            global total_balance
            total_balance += balance  # 累计总余额

            # 检查余额是否未增长和是否为0
            conn_local = sqlite3.connect(db_file)
            cur_local = conn_local.cursor()
            cur_local.execute('SELECT balance FROM balances WHERE address = ? AND date = ?', (address, yesterday_date))
            prev_balance = cur_local.fetchone()
            if prev_balance and balance <= prev_balance[0]:
                not_increased_lines.append(addresses.index(address) + 1)
            if balance == 0:
                zero_balance_lines.append(addresses.index(address) + 1)
            conn_local.close()

    # 输出结果
    print(f"Total balance: {total_balance / 1000000:.2f} Million")
    if not_increased_lines:
        print(f"Addresses with no increase in balance: {','.join(map(str, not_increased_lines))}")
    if zero_balance_lines:
        print(f"Zero balance lines: {','.join(map(str, zero_balance_lines))}")

if __name__ == "__main__":
    main()
