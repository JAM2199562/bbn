import subprocess
import sys

# 配置 RPC 参数
rpcuser = 'nextdao'
rpcpassword = 'nextdao'
rpcport = '38332'  # Signet 默认 RPC 端口

# 基础 RPC 命令
bitcoin_cli_base = f"bitcoin-cli -signet -rpcuser={rpcuser} -rpcpassword={rpcpassword} -rpcport={rpcport}"

def query_balance():
    try:
        balance = subprocess.check_output(f"{bitcoin_cli_base} getbalance", shell=True, text=True)
        return float(balance.strip())
    except subprocess.CalledProcessError as e:
        print(f"查询余额时出错: {e}")
        return None

def send_transaction(target_address, amount):
    try:
        txid = subprocess.check_output(f"{bitcoin_cli_base} sendtoaddress {target_address} {amount}", shell=True, text=True).strip()
        print(f"转账成功，交易ID: {txid}")
    except subprocess.CalledProcessError as e:
        print(f"发送交易失败: {e}")

def main():
    # 从文件中读取地址
    addresses = []
    with open("signet_addr.txt", "r") as file:
        addresses = [line.strip() for line in file if line.strip()]

    # 获取用户输入的转账金额
    try:
        amount = float(input("请输入每个地址转账的金额（BTC）: "))
    except ValueError:
        print("输入的金额无效。")
        sys.exit(1)

    # 查询当前余额
    balance = query_balance()
    if balance is None:
        print("无法获取余额，终止执行。")
        sys.exit(1)

    for address in addresses:
        if balance >= amount:
            print(f"正在向 {address} 转账 {amount} BTC...")
            send_transaction(address, amount)
            balance -= amount  # 更新余额
        else:
            print(f"余额不足，无法向 {address} 转账 {amount} BTC。当前余额: {balance} BTC")
            break  # 余额不足时停止执行

if __name__ == "__main__":
    main()

