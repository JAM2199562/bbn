#!/bin/bash

# 获取节点ID并去除双引号
node_id=$(babylond status | jq -r .node_info.id)

# 获取IP地址
ip=$(curl -s ip.sb)

# 获取监听的端口号，假设您是在寻找以656开头的端口
port=$(netstat -tlnp | grep 656 | awk '{print $4}' | rev | cut -d':' -f1 | rev)

# 拼接字符串并在最后加上逗号
result="${node_id}@${ip}:${port},"

# 打印结果
echo $result
