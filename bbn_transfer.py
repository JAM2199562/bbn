import re
import subprocess
import sys
import pexpect
# 定义一个字典来存储配置项
config = {}

# 打开并读取 local.conf 文件
with open('local.conf', 'r') as file:
    for line in file:
        # 移除字符串两端的空白符（包括换行符）
        line = line.strip()
        # 跳过空行和注释行
        if not line or line.startswith('#'):
            continue
        # 分割键和值
        key, value = line.split('=', 1)
        # 去除键和值两端的空白符，并将它们添加到配置字典中
        config[key.strip()] = value.strip()

# 现在你可以从 config 字典中获取 'password'
password = config.get('password', '')  # 使用默认值以防 'password' 不存在
def query_balance(address):
    try:
        raw_output = subprocess.check_output(["babylond", "query", "bank", "balances", address], text=True)
        print(f"原始输出: {raw_output}")
        match = re.search(r'amount: "(\d+)"', raw_output)
        if match:
            return int(match.group(1))
    except subprocess.CalledProcessError as e:
        print(f"执行命令时出错: {e}")
    return None

def send_transaction(address, target_address, amount, password):
    # 检查是否尝试向相同的地址发送资金
    if address == target_address:
        print("发送地址和接收地址相同，跳过转账操作。")
        return  # 直接返回，不执行后续代码
    
    command = f"babylond tx bank send {address} {target_address} {amount}ubbn --gas=auto --gas-adjustment=2 --gas-prices=0.0025ubbn --chain-id=bbn-test-3 -y"
    try:
        # 使用pexpect.spawn运行命令
        child = pexpect.spawn(command, encoding='utf-8', timeout=30)
        child.logfile = sys.stdout  # 可以看到实时输出，方便调试

        # 等待密码提示
        child.expect('Enter keyring passphrase \(attempt 1/3\):')
        
        # 输入密码
        child.sendline(password)
        
        # 等待命令执行完成
        child.expect(pexpect.EOF)
        
        print("交易已发送。")
    except pexpect.exceptions.TIMEOUT:
        print("发送交易时超时。")
    except pexpect.exceptions.EOF:
        print("在完成交易之前，进程意外结束。")
    except Exception as e:
        print(f"发送交易失败: {e}")

def main():
    target_address = "bbn15u5yydxl6qjs02w8u6u9mvh8u5hlwqgs8jdu9j"
    try:
        transfer_amount = float(input("请输入转账金额（BBN）: "))
    except ValueError:
        print("输入的不是有效的数字。")
        sys.exit(1)

    amount_in_micro = int(transfer_amount * 1_000_000)  # 将BBN转换为微BBN

    with open("bbn_addr.txt", "r") as file:
        for address in file:
            address = address.strip()
            print(f"处理地址 {address}...")
            balance = query_balance(address)

            if balance is None or not isinstance(balance, int):
                print(f"未能为地址 {address} 获取有效余额。")
                continue

            if balance >= amount_in_micro:
                print(f"准备从 {address} 发送 {transfer_amount} BBN 到 {target_address}...")
                send_transaction(address, target_address, str(amount_in_micro))
            else:
                print(f"{address} 的余额不足以发送。余额为：{balance / 1_000_000} BBN")

if __name__ == "__main__":
    main()
