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

# # 文件名
# balance_file = f"balances_record_{current_date}.txt"
# yesterday_balance_file = f"balances_record_{yesterday_date}.txt"

# # 清空当前余额文件
# open(balance_file, 'w').close()

# 初始化总余额和行号记录
total_balance = 0
not_increased_lines = []
zero_balance_lines = []

# 假设原始的 addresses 列表只包含地址
# 将其转换为包含 (行号, 地址) 的元组列表
addresses_with_line_numbers = [(i + 1, address) for i, address in enumerate(addresses)]

# 用于提取余额的正则表达式
balance_pattern = re.compile(r'- amount: "(\d+)"')

# 查询余额的函数
def query_balance(line_address):
    # 解包行号和地址
    line_number, address = line_address

    # 在每个线程内部创建数据库连接
    conn_local = sqlite3.connect(db_file)
    cur_local = conn_local.cursor()

    try:
        # 执行外部命令获取余额
        result = subprocess.run(['babylond', 'query', 'bank', 'balances', address, '--log_format', 'json'], capture_output=True, text=True)
        
        # 使用正则表达式提取余额
        balance_match = balance_pattern.search(result.stdout)
        # 转换为标准单位
        balance = int(balance_match.group(1)) / 1_000_000 if balance_match else 0

        # 输出当前正在处理的地址和查询到的余额
        print(f"第 {line_number:3} 行的地址: {address}，余额为: {balance:>10.6f}")

    except Exception as e:
        balance = 0  # 在遇到异常时设置余额为0
        # 输出当前正在处理的地址和异常信息
        print(f"第 {line_number} 行的地址: {address}，查询过程中遇到错误: {e}")

    # 更新数据库
    cur_local.execute('INSERT OR REPLACE INTO balances (address, balance, date) VALUES (?, ?, ?)', (address, balance, current_date))
    conn_local.commit()

    # 关闭数据库连接
    conn_local.close()

    return address, balance

# 主程序
def main():
    init_db()  # 初始化数据库
    futures = []
    results = []

    with ThreadPoolExecutor(max_workers=2) as executor:
        # 提交所有查询到线程池
        for line_address in addresses_with_line_numbers:
            # 将包含行号和地址的元组提交给线程池
            future = executor.submit(query_balance, line_address)
            futures.append(future)

        # 获取结果
        for future in futures:
            address, balance = future.result()
            results.append((address, balance))

            # 余下的逻辑处理
            global total_balance
            total_balance += balance  # 累计总余额

            # 检查余额是否未增长和是否为0
            conn_local = sqlite3.connect(db_file)
            cur_local = conn_local.cursor()
            cur_local.execute('SELECT balance FROM balances WHERE address = ? AND date = ?', (address, yesterday_date))
            prev_balance = cur_local.fetchone()
            if prev_balance and balance <= prev_balance[0]:
                # 注意这里我们用 address 来获取原始行号
                not_increased_lines.append(addresses_with_line_numbers.index((addresses.index(address) + 1, address)) + 1)
            if balance == 0:
                # 同上
                zero_balance_lines.append(addresses_with_line_numbers.index((addresses.index(address) + 1, address)) + 1)
            conn_local.close()

    # 输出结果
    print(f"Total balance: {total_balance:.2f}")
    if not_increased_lines:
        print(f"Addresses with no increase in balance: {','.join(map(str, not_increased_lines))}")
    if zero_balance_lines:
        print(f"Zero balance lines: {','.join(map(str, zero_balance_lines))}")

if __name__ == "__main__":
    main()
