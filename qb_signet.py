import requests

def get_balance_for_addresses(filename):
    total_balance = 0  # 用于汇总所有地址的余额
    low_balance_lines = []  # 用于存储余额小于5000的行号

    with open(filename, 'r') as file:
        addresses = file.readlines()

        for line_number, address in enumerate(addresses, start=1):
            address = address.strip()  # 去除换行符和前后的空格
            if address.startswith("#") or not address:
                continue  # 跳过被注释掉的行和空行

            url = f'https://mempool.space/signet/api/address/{address}'  # 构造请求URL
            response = requests.get(url)  # 发送请求并获取响应

            if response.status_code == 200:
                data = response.json()
                funded_sum = data.get('chain_stats', {}).get('funded_txo_sum', 0)
                spent_sum = data.get('chain_stats', {}).get('spent_txo_sum', 0)
                balance = funded_sum - spent_sum  # 计算余额

                total_balance += balance  # 更新总余额
                if balance < 5000:  # 检查余额是否小于5000聪
                    low_balance_lines.append(line_number)  # 添加行号到列表

                # 打印行号，地址和余额
                print(f'行号: {line_number}, 地址: {address}, 余额: {balance}')
            else:
                print(f'行号: {line_number}, 地址: {address}, 错误: 获取数据出错')

    # 打印总余额，转换为比特币单位（1比特币 = 100,000,000聪）
    print(f'总余额: {total_balance / 100000000:.8f} BTC')

    # 打印余额小于5000聪的行号
    if low_balance_lines:
        print(f'余额小于5000聪的行号: {", ".join(map(str, low_balance_lines))}')
    else:
        print('没有余额小于5000聪的地址。')

# 运行函数
get_balance_for_addresses('sig_addr.txt')

