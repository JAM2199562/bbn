#!/bin/bash

# 从文件读取地址到数组
readarray -t addresses < bbn_addr.txt

# 获取当前日期和昨天的日期作为文件后缀，确保每天一个文件
current_date=$(date +%Y-%m-%d)
yesterday_date=$(date -d "yesterday" +%Y-%m-%d)

balance_file="balances_record_${current_date}.txt"
yesterday_balance_file="balances_record_${yesterday_date}.txt"

# 每次运行脚本时覆写当天的余额文件，以保持文件内只有一份最新记录
> "$balance_file"

# 初始化总余额变量
total_balance=0

# 用于记录余额未发生增长的地址行号
not_increased_lines=""

# 用于记录余额为0的地址行号
zero_balance_lines=""

# 遍历地址数组
for i in "${!addresses[@]}"; do
    address=${addresses[$i]}
    # echo "Querying balance for: $address"
    
    # 假设的命令查询余额，根据你的实际命令替换
    balance_raw=$(babylond query bank balances "$address" --log_format json | grep "amount:" | cut -d '"' -f 2)
    balance="${balance_raw:-0}"  # 如果balance_raw为空，则默认为0
    
    # 检查余额是否是有效数字
    if ! [[ "$balance" =~ ^[0-9]+$ ]]; then
        echo "Invalid balance for $address, setting balance to 0"
        balance=0
    fi
    
    echo "Balance for $address: $balance"
    
    # 记录当前运行时的余额到当天的余额文件
    echo "$address $balance" >> "$balance_file"

    # 累加余额到总余额
    total_balance=$((total_balance + balance))

    # 如果昨天的余额文件存在，则与昨天的余额进行对比
    if [ -f "$yesterday_balance_file" ]; then
        prev_balance=$(grep "$address" "$yesterday_balance_file" | cut -d ' ' -f 2)
        # 检查余额是否未发生增长（余额减少或保持不变）
        if [ -z "$prev_balance" ] || [ "$balance" -le "$prev_balance" ]; then
            not_increased_lines="${not_increased_lines:+$not_increased_lines,}$((i + 1))"
        fi
    else
        echo "No balance file from yesterday to compare."
    fi

    # 检查余额是否为0
    if [ "$balance" -eq 0 ]; then
        zero_balance_lines="${zero_balance_lines:+$zero_balance_lines,}$((i + 1))"
    fi
done

# 显示总余额，以1000000为比率
echo "Total balance: $(echo "scale=2; $total_balance / 1000000" | bc)"

# 输出余额未发生增长的地址行号
if [ ! -z "$not_increased_lines" ]; then
    echo "Addresses with no increase in balance: $not_increased_lines"
fi

# 输出余额为0的地址行号
if [ ! -z "$zero_balance_lines" ]; then
    echo "Zero balance lines: $zero_balance_lines"
fi
