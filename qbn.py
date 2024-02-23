import datetime
import os
import time
import requests
from datetime import datetime, timedelta

import json

def query_api_for_latest_transaction(address):
    url = f'https://babylon.api.explorers.guru/api/v1/accounts/{address}/txs?limit=5&category=transfer'
    headers = {
        'accept': '*/*',
        'origin': 'https://babylon.explorers.guru',
        'referer': f'https://babylon.explorers.guru/account/{address}',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'
    }
    try:
        # print(f"Sending request to {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises stored HTTPError, if one occurred.
        
        # print("API request successful.")
        data = response.json()
        
        # Debug: Print the first few transactions for inspection
        # print("API response data:", json.dumps(data['data'][:3], indent=4, ensure_ascii=False))
        
        # Filter transactions where any message tokens amount equals "1100000"
        transactions = [
            tx for tx in data.get('data', []) 
            if any(
                msg.get('tokens', {}).get('amount') == '1100000' or msg.get('tokens', {}).get('amount') == 1100000
                for msg in tx.get('messages', [])
            )
        ]
        
        if transactions:
            latest_transaction = sorted(transactions, key=lambda tx: tx['timestamp'], reverse=True)[0]
            print(f"Found latest transaction time: {latest_transaction['timestamp']}")
            return latest_transaction['timestamp']
        else:
            print("No matching transactions found.")
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
    except ValueError as e:
        print(f"Error processing API response: {e}")
    return None

def time_to_24h_mark(last_tx_timestamp, current_time):
    """计算从最后一次交易到24小时的剩余时间（秒）"""
    time_passed = (current_time - last_tx_timestamp).total_seconds()
    return 86400 - time_passed  # 24小时 = 86400秒

def predict_reaching_time(remaining_times, address_count, current_time_utc):
    """
    预测将有指定数量的地址达到24小时无新交易状态的时间，并以GMT+8显示结果。

    :param remaining_times: 所有地址到达24小时标记的剩余时间列表
    :param address_count: 指定的地址数量
    :param current_time_utc: 当前时间的datetime对象（假设为UTC）
    """
    if address_count < 1:
        print("地址数量必须至少为1。")
        return

    future_remaining_times = [t for t in remaining_times if t > 0]

    if len(future_remaining_times) >= address_count:
        sorted_remaining_times = sorted(future_remaining_times)
        time_for_target_to_reach_24h = sorted_remaining_times[address_count - 1]
        # print(f"找到的 time_for_target_to_reach_24h: {time_for_target_to_reach_24h} 秒后")

        future_time_for_target_utc = current_time_utc + timedelta(seconds=time_for_target_to_reach_24h)
        future_time_for_target_gmt8 = future_time_for_target_utc + timedelta(hours=8)
        print(f"预计在 {future_time_for_target_gmt8.strftime('%Y-%m-%d %H:%M')} 时，将有{address_count}个地址可以继续领水。")
    else:
        print(f"当前少于{address_count}个地址接近24小时无新交易状态。")

def query_balance_via_os(address):
    """
    使用os.popen执行外部命令来查询地址的余额，并将结果转换为主单位。
    """
    command = f'babylond query bank balances "{address}" --log_format json'
    try:
        with os.popen(command) as f:
            output = f.read()
        # 解析输出以找到余额值
        balance_raw = [line.strip() for line in output.split('\n') if "amount:" in line]
        if balance_raw:
            # 由于可能有多个 "amount:" 出现，取第一个，并从该行提取数字
            balance_str = balance_raw[0].split(':')[1].strip().strip('"')
            # 将余额转换为整数，并除以1,000,000进行单位转换
            balance = int(balance_str) / 1000000
        else:
            balance = 0.0
    except Exception as e:
        print(f"查询地址 {address} 的余额时出错: {e}")
        balance = 0.0
    return balance


def sum_balances_via_os(addresses):
    """
    计算并返回所有给定地址的余额总和。
    """
    total_balance = 0
    for address in addresses:
        balance = query_balance_via_os(address)
        total_balance += balance
        # print(f"地址 {address} 的余额为: {balance}")
    return total_balance
# 从文件中读取地址
addresses = []
with open('bbn_addr.txt', 'r') as file:
    addresses = file.read().splitlines()

# 从文件中读取地址
addresses = []
with open('bbn_addr.txt', 'r') as file:
    addresses = file.read().splitlines()
# 仅处理前100个地址
# addresses = addresses[:100]

# 定义用于存储最后交易时间的文件名
last_tx_file = "last_transactions.txt"

# 获取当前UTC时间的Unix时间戳
current_time_utc = datetime.utcnow()

# 定义GMT+8到UTC的时间差（秒），GMT+8比UTC快8小时
time_diff_gmt8_to_utc = 8 * 3600

# 用于记录超过24小时没有新交易的地址行号
inactive_lines = []

# 检查并创建最后一次交易时间文件，如果它不存在
if not os.path.exists(last_tx_file):
    open(last_tx_file, 'w').close()

# 从文件加载最后交易时间
last_transactions = {}
try:
    with open(last_tx_file, 'r') as file:
        last_transactions = {line.split(' ')[0]: ' '.join(line.split(' ')[1:]) for line in file.read().splitlines()}
except FileNotFoundError:
    last_transactions = {}

# 初始化一个列表来收集在最后24小时内没有新交易的地址的行号
inactive_addresses_indices = []

# 初始化列表，收集所有地址到达24小时标记的剩余时间
remaining_times_to_24h = []

# 主循环，检查每个地址并查询余额
total_balance = 0  # 初始化余额总和
for i, address in enumerate(addresses):
    print("--------------------------------------------------------------------------------")
    print(f"检查第 {i + 1} 行地址的最后一次交易和查询余额: {address}")
    
    # 特殊地址处理
    if address == 'bbn15u5yydxl6qjs02w8u6u9mvh8u5hlwqgs8jdu9j':
        # print(f"归集地址 {address} 跳过联网查询和更新本地文件，只累加余额。")
        balance = query_balance_via_os(address)
        total_balance += balance
        print(f"归集地址 {address} 的余额为: {balance}")
        continue

    last_tx_time = last_transactions.get(address, "")
    current_time_utc = datetime.utcnow()
    force_update = False

    if last_tx_time == 'None' or not last_tx_time:
        force_update = True
    else:
        try:
            last_tx_timestamp = datetime.strptime(last_tx_time, "%Y-%m-%dT%H:%M:%S.%fZ")
            time_diff = (current_time_utc - last_tx_timestamp).total_seconds()
            if time_diff <= 86400:
                print(f"缓存时间小于24小时，使用缓存数据: {address}")
                # 即使使用缓存数据，也计算到达24小时标记的剩余时间
                remaining_times_to_24h.append(86400 - time_diff)
            else:
                force_update = True
        except ValueError as e:
            force_update = True

    if force_update:
        latest_time = query_api_for_latest_transaction(address)
        if latest_time:
            last_transactions[address] = latest_time
            latest_time_dt = datetime.strptime(latest_time, "%Y-%m-%dT%H:%M:%S.%fZ")
            time_diff = (current_time_utc - latest_time_dt).total_seconds()
            remaining_times_to_24h.append(86400 - time_diff)
            if time_diff > 86400:
                # 如果该地址在最后24小时内无新交易，记录其行号
                inactive_addresses_indices.append(i + 1)
        else:
            print("没有查询到符合条件的交易。")
            last_transactions[address] = 'None'

    # 为非特殊地址查询余额并累加到总余额
    if address != 'bbn15u5yydxl6qjs02w8u6u9mvh8u5hlwqgs8jdu9j':
        balance = query_balance_via_os(address)
        total_balance += balance
        print(f"地址 {address} 的余额为: {balance}")

# 更新最后交易时间文件，排除归集地址
with open(last_tx_file, 'w') as file:
    for address, time in last_transactions.items():
        if address != 'bbn15u5yydxl6qjs02w8u6u9mvh8u5hlwqgs8jdu9j':
            file.write(f"{address} {time}\n")


if inactive_addresses_indices:
    print("在最后24小时内没有新交易的地址行号:", ",".join(map(str, inactive_addresses_indices)))
else:
    print("所有地址在最近24小时内都有交易。")

# 输出总余额
print(f"所有地址的余额总和为: {total_balance}")
# 示例使用
current_time_utc = datetime.utcnow()  # 正确的方法调用
predict_reaching_time(remaining_times_to_24h, 25, current_time_utc) 