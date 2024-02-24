#!/bin/bash
Crontab_file="/usr/bin/crontab"
Green_font_prefix="\033[32m"
Red_font_prefix="\033[31m"
Green_background_prefix="\033[42;37m"
Red_background_prefix="\033[41;37m"
Font_color_suffix="\033[0m"
Info="[${Green_font_prefix}信息${Font_color_suffix}]"
Error="[${Red_font_prefix}错误${Font_color_suffix}]"
Tip="[${Green_font_prefix}注意${Font_color_suffix}]"

CHAIN_ID="bbn-test-3"
cd /root
check_root() {
    [[ $EUID != 0 ]] && echo -e "${Error} 当前非ROOT账号(或没有ROOT权限), 无法继续操作, 请更换ROOT账号或使用 ${Green_background_prefix}sudo su${Font_color_suffix} 命令获取临时ROOT权限（执行后可能会提示输入当前账号的密码）。" && exit 1
}

install_go() {
    check_root
    # Install dependencies for building from source
    sudo apt update
    sudo apt install -y curl git jq lz4 build-essential

    # Install Go
    sudo rm -rf /usr/local/go
    curl -L https://go.dev/dl/go1.21.6.linux-amd64.tar.gz | sudo tar -xzf - -C /usr/local
    echo 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin' >> $HOME/.bashrc
    source .bashrc
}

install_babylon_env() {
    read -e -p "请输入你的节点名称: " node_name
    install_go

    # Clone project repository
    cd && rm -rf babylon
    git clone https://github.com/babylonchain/babylon
    cd babylon
    git checkout v0.8.3
    
    # Build binary
    make install
    export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin
    # Set node CLI configuration
    # babylond config chain-id bbn-test-3
    # babylond config keyring-backend test
    # babylond config node tcp://localhost:20657

    # Initialize the node
    babylond init "$node_name" --chain-id bbn-test-3

        # testnet-3的genesis
        wget https://github.com/babylonchain/networks/raw/main/bbn-test-3/genesis.tar.bz2
        tar -xjf genesis.tar.bz2 && rm genesis.tar.bz2
        mv genesis.json ~/.babylond/config/genesis.json
        cd && cp bbn/bashrc_babylon $HOME/
        echo "source bashrc_babylon" >> $HOME/.bashrc

    # Download genesis and addrbook files
    # curl -L https://snapshots-testnet.nodejumper.io/babylon-testnet/genesis.json > $HOME/.babylond/config/genesis.json
    # curl -L https://snapshots-testnet.nodejumper.io/babylon-testnet/addrbook.json > $HOME/.babylond/config/addrbook.json

    # Set seeds
    sed -i -e 's|^seeds *=.*|seeds = "49b4685f16670e784a0fe78f37cd37d56c7aff0e@3.14.89.82:20656,9cb1974618ddd541c9a4f4562b842b96ffaf1446@3.16.63.237:26656,1ecc4a9d703ad52d16bf30a592597c948c115176@165.154.244.14:26656,0ccb869ba63cf7730017c357189d01b20e4eb277@185.84.224.125:20656,5463943178cdb57a02d6d20964e4061dfcf0afb4@142.132.154.53:20656,b82b321380d1d949d1eed6da03696b1b2ef987ba@148.251.176.236:3000,49b15e202497c231ebe7b2a56bb46cfc60eff78c@135.181.134.151:46656,3774fb9996de16c2f2280cb2d938db7af88d50be@162.62.52.147:26656,26cb133489436035829b6920e89105046eccc841@178.63.95.125:26656,326fee158e9e24a208e53f6703c076e1465e739d@193.34.212.39:26659,868730197ee267db3c772414ec1cd2085cc036d4@148.251.235.130:17656,9d840ebd61005b1b1b1794c0cf11ef253faf9a84@43.157.95.203:26656"|' $HOME/.babylond/config/config.toml

    # Set minimum gas price
    sed -i -e 's|^minimum-gas-prices *=.*|minimum-gas-prices = "0.00001ubbn"|' $HOME/.babylond/config/app.toml

    # Set pruning
    sed -i \
    -e 's|^pruning *=.*|pruning = "custom"|' \
    -e 's|^pruning-keep-recent *=.*|pruning-keep-recent = "100"|' \
    -e 's|^pruning-interval *=.*|pruning-interval = "17"|' \
    $HOME/.babylond/config/app.toml

    # Set additional configs
    sed -i 's|^network *=.*|network = "signet"|g' $HOME/.babylond/config/app.toml

    # Change ports
    sed -i -e "s%:1317%:20617%; s%:8080%:20680%; s%:9090%:20690%; s%:9091%:20691%; s%:8545%:20645%; s%:8546%:20646%; s%:6065%:20665%" $HOME/.babylond/config/app.toml
    sed -i -e "s%:26658%:20658%; s%:26657%:20657%; s%:6060%:20660%; s%:26656%:20656%; s%:26660%:20661%" $HOME/.babylond/config/config.toml
    sed -i -e "s%:26657%:20657%" $HOME/.babylond/config/client.toml

    curl -L "http://138.68.47.27:6080/public/babylond.tar.gz" | tar -xz -C "$HOME"

    # Create a service
    sudo tee /etc/systemd/system/babylond.service > /dev/null << EOF
[Unit]
Description=Babylon node service
After=network-online.target
[Service]
User=$USER
ExecStart=$(which babylond) start
Restart=on-failure
RestartSec=10
LimitNOFILE=65535
[Install]
WantedBy=multi-user.target
EOF

    sed -i -e "s|^key-name *=.*|key-name = \"wallet\"|" ~/.babylond/config/app.toml
    sed -i -e "s|^timeout_commit *=.*|timeout_commit = \"10s\"|" ~/.babylond/config/config.toml
    echo -e "\033[36m请自行运行如下指令导入钱包并创建bls key\033[0m" 
    echo -e "\033[35mbabylond keys add wallet --recover \033[0m"
    echo -e "\033[35mbabylond create-bls-key \$(babylond keys show wallet -a)\033[0m"
    sudo systemctl daemon-reload
    sudo systemctl enable babylond.service
}

start_babylon_node() {
    # Start the service and check the logs
    sudo systemctl restart babylond.service
    sudo journalctl -u babylond.service -f --no-hostname -o cat
}

check_node_status_and_height() {
    babylond status | jq .SyncInfo
    systemctl status babylond
}

get_log() {
    sudo journalctl -u babylond.service -f --no-hostname -o cat
}

start_validator_node() {
    read -e -p "请输入你的验证者名称: " validator_name
    babylond tx checkpointing create-validator \
    --amount="1000000ubbn" \
    --pubkey=$(babylond tendermint show-validator) \
    --moniker="$validator_name" \
    --chain-id="bbn-test-3" \
    --gas="auto" \
    --gas-adjustment=1.2 \
    --gas-prices="0.0025ubbn" \
    --keyring-backend=test \
    --from="wallet" \
    --commission-rate="0.10" \
    --commission-max-rate="0.20" \
    --commission-max-change-rate="0.01" \
    --min-self-delegation="1"
}

echo && echo -e " ${Red_font_prefix}babylon节点 一键安装脚本${Font_color_suffix} by \033[1;35moooooyoung\033[0m
此脚本完全免费开源, 由推特用户 ${Green_font_prefix}@ouyoung11开发${Font_color_suffix},
欢迎关注, 如有收费请勿上当受骗。
 ———————————————————————
 ${Green_font_prefix} 1.安装babylon节点环境 ${Font_color_suffix}
 ${Green_font_prefix} 2.运行babylon节点 ${Font_color_suffix}
 ${Green_font_prefix} 3.检查节点同步高度及状态 ${Font_color_suffix}
 ${Green_font_prefix} 4.显示同步日志 ${Font_color_suffix}
 ${Green_font_prefix} 5.成为验证者（需要等节点同步到最新区块） ${Font_color_suffix}
 ———————————————————————" && echo
read -e -p " 请参照教程执行以上步骤，请输入数字 [1-5]:" num
case "$num" in
1)
    install_babylon_env
    ;;
2)
    start_babylon_node
    ;;
3)
    check_node_status_and_height
    ;;
4)
    get_log
    ;;
5)
    start_validator_node
    ;;
*)
    echo
    echo -e " ${Error} 请输入正确的数字"
    ;;
esac

