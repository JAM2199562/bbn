#!/usr/bin/env python3

"""
区块链高度监控脚本

此脚本通过向本地节点的状态端点发送HTTP请求来监控区块链的高度。
它每30秒检查一次区块链高度。如果区块链高度在5分钟内没有变化，
它会尝试通过发送SIGTERM信号来优雅地停止'babylond'进程，然后等待3分钟以允许它优雅地关闭。
如果在这段时间后'babylond'进程还没有停止，它会强制使用SIGKILL信号终止进程。
一旦进程停止，脚本将重新启动它。脚本使用ANSI颜色代码来突出显示关于区块链更新和监控状态的消息，
以便更好地可视化。

要求:
- Python 3
- Python的'requests'库
- 本地机器上运行的'babylond'进程
- 脚本必须具有足够的权限来停止和启动'babylond'进程。
"""

import requests
import time
import subprocess

# ANSI颜色代码
GREEN = '\033[92m'  # 绿色文本
YELLOW = '\033[93m'  # 黄色文本
RESET = '\033[0m'   # 重置颜色

# 初始设置
last_block_height = None  # 存储上一次的区块高度
last_change_time = None  # 最后一次区块高度变化的时间
check_interval = 30  # 检查间隔，单位：秒
change_duration = 300  # 变化检查时长，单位：秒（5分钟）
shutdown_duration = 180  # 给予一定时间以优雅地关闭，单位：秒（3分钟）
restart_delay = 1800  # 重启后的延迟时间，单位：秒（30分钟）
last_restart_time = time.time() - restart_delay  # 上一次重启的时间，初始化以允许立即执行检查

while True:
    current_time = time.time()
    # 使用requests库执行HTTP请求
    response = requests.get('http://localhost:26657/status')
    data = response.json()
    latest_block_height = data['result']['sync_info']['latest_block_height']

    # 打印当前区块高度
    print(f"当前区块高度: {latest_block_height}")

    # 高度变化时更新记录，否则检查是否超时未变化
    if last_block_height is None or latest_block_height != last_block_height:
        print(GREEN + "区块高度正在更新。" + RESET)
        last_block_height = latest_block_height
        last_change_time = current_time
    elif current_time - last_change_time >= change_duration and current_time - last_restart_time >= restart_delay:
        # 高度在5分钟内没有变化，并且距离上次重启已经超过30分钟
        print(YELLOW + "没有发现区块高度的变化，尝试优雅地停止babylond进程。" + RESET)
        subprocess.run(['pkill', '-15', 'babylond'])  # 发送SIGTERM信号尝试优雅地停止babylond
        time.sleep(shutdown_duration)  # 给予一定时间以优雅地关闭

        # 检查进程是否仍在运行，如果是，则发送SIGKILL信号强制终止
        if subprocess.run(['pgrep', '-x', 'babylond'], capture_output=True).stdout:
            print("强制停止babylond进程。")
            subprocess.run(['pkill', '-9', 'babylond'])

        # 等待进程结束
        time.sleep(5)

        # 确认所有babylond进程都已经结束
        if not subprocess.run(['pgrep', '-x', 'babylond'], capture_output=True).stdout:
            print("所有babylond进程已结束，现在重新启动。")
            subprocess.run(['babylond', 'start'])
            last_restart_time = time.time()
        else:
            print("还有babylond进程在运行。")
    else:
        print(YELLOW + "区块高度未发生变化，继续监测。" + RESET)

    time.sleep(check_interval)
