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
    export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin
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
    make build

    # Prepare directories
    mkdir -p ~/.babylond
    mkdir -p ~/.babylond/cosmovisor
    mkdir -p ~/.babylond/cosmovisor/genesis
    mkdir -p ~/.babylond/cosmovisor/genesis/bin
    mkdir -p ~/.babylond/cosmovisor/upgrades

    # Install Cosmovisor
    go install cosmossdk.io/tools/cosmovisor/cmd/cosmovisor@latest

    # Move BabylonD file to Cosmovisor directory
    mv build/babylond $HOME/.babylond/cosmovisor/genesis/bin/
    rm -rf build

    # Create application symlinks
    sudo ln -s $HOME/.babylond/cosmovisor/genesis $HOME/.babylond/cosmovisor/current -f
    sudo ln -s $HOME/.babylond/cosmovisor/current/bin/babylond /usr/local/bin/babylond -f

    # Initialize the node
    babylond init $node_name --chain-id $CHAIN_ID

    # Download genesis
    wget https://github.com/babylonchain/networks/raw/main/bbn-test-3/genesis.tar.bz2
    tar -xjf genesis.tar.bz2 && rm genesis.tar.bz2
    mv genesis.json ~/.babylond/config/genesis.json

    # Add seeds
    sed -i -e 's|^seeds *=.*|seeds = "49b4685f16670e784a0fe78f37cd37d56c7aff0e@3.14.89.82:26656,9cb1974618ddd541c9a4f4562b842b96ffaf1446@3.16.63.237:26656"|' $HOME/.babylond/config/config.toml

    # Change network to signet:
    sed -i -e "s|^\(network = \).*|\1\"signet\"|" $HOME/.babylond/config/app.toml

    # pruning settings
    sed -i 's/pruning = "default"/pruning = "everything"/g' $HOME/.babylond/config/app.toml
    sed -i 's/min-retain-blocks = 0/min-retain-blocks = 100/g' $HOME/.babylond/config/app.toml

    # Set minimum gas price:
    sed -i -e "s|^minimum-gas-prices *=.*|minimum-gas-prices = \"0.00001ubbn\"|" $HOME/.babylond/config/app.toml

    # Set peers:
    PEERS="54474d2722d33397b2f27f27becd508efdb58584@195.154.91.140:16456,1a87d7c7909736e6664a3645d42d494209297263@46.180.223.102:26656,72340e46d17c407a3f492c9eae13106f3211800b@95.216.21.168:35656,2f071c6216579a0c2224d22311c92bf24ed8d742@84.247.170.76:26656,e5066f71c5139556bbdee7fc7f82fc08ff6293b5@185.202.239.204:26656,a3b57c4a5f06ae5876abf8d4294de4a320fb5e0f@194.163.166.144:26656,63aa2422fae1ae979ddeefaf6f675a398d3c8ffc@38.242.141.90:26656,28afb978b6cfd581da4505398fbc755ee83d3858@65.109.30.35:20656,d968bf54d4005796d77ef54d032aa258c73d29ea@81.27.244.79:26656,67aeeee9d253fc38f4e522bf77bf76386f954fa5@135.181.200.64:26656,05de273427e9b6f1e0f51d14ba8cad8216c57d16@34.83.252.122:26656,d0893daee4fd97d620a549fe329c71319305d897@95.216.25.29:35656,55dcd33771637bc3a1d9015187b491f5bec2f049@89.117.49.23:26656,40662747f0e01678dbdf1e50879f40a68139d7aa@35.163.58.204:26656,64e52da64491fcd61a199cbc2684d2886d66dcf4@183.208.183.225:26656,9a2ce575cf11cd301f2756f0ddb0b3d3101b3a67@88.99.213.25:41656,a787ca46d620c3215a043b1bdab66c1a307463db@109.199.117.130:26656,9b445464f284da5a9f9378984ba58bf33091dc9b@65.108.101.37:35656,0c3f306dcb336c3a1ec8c4d7c84bd27076cfeac4@66.94.107.124:26656,2a48cab6265889d43f6ed54e05cfaeab27ada274@161.97.157.215:26656,5e865ee61f51c76f13e819218a0894e17c2d03a9@156.224.26.196:26656"
    sed -i 's|^persistent_peers *=.*|persistent_peers = "'$PEERS'"|' $HOME/.babylond/config/config.toml
    # download snapshoots
    # curl -L "http://138.68.47.27:6080/public/babylond.tar.gz" | tar -xz -C "$HOME"
    # Create a service
    sudo tee /etc/systemd/system/babylond.service > /dev/null <<EOF
[Unit]
Description=Babylon daemon
After=network-online.target

[Service]
User=$USER
ExecStart=$(which cosmovisor) run start --x-crisis-skip-assert-invariants
Restart=always
RestartSec=3
LimitNOFILE=infinity

Environment="DAEMON_NAME=babylond"
Environment="DAEMON_HOME=${HOME}/.babylond"
Environment="DAEMON_RESTART_AFTER_UPGRADE=true"
Environment="DAEMON_ALLOW_DOWNLOAD_BINARIES=false"

[Install]
WantedBy=multi-user.target
EOF
    
    echo -e "\n"
    echo -e "下面开始创建babylon钱包，会让你创建一个钱包密码..."
    # babylond keys add wallet
    sed -i -e "s|^key-name *=.*|key-name = \"wallet\"|" ~/.babylond/config/app.toml
    sed -i -e "s|^timeout_commit *=.*|timeout_commit = \"30s\"|" ~/.babylond/config/config.toml
    # babylond create-bls-key $(babylond keys show wallet -a)
    cat $HOME/.babylond/config/priv_validator_key.json
    echo -e "\n"
    echo -e "本程序修改为需要手动导入钱包，创建bls key ..."

    sudo -S systemctl daemon-reload
    sudo -S systemctl enable babylond
    cp $HOME/bbn/bashrc_babylon $HOME/bashrc_babylon
    echo 'source bashrc_babylon' >> $HOME/.bashrc
}

start_babylon_node() {
    # Start the service and check the logs
    sudo -S systemctl restart babylond
    sudo journalctl -u babylond.service -f --no-hostname -o cat
}

check_node_status_and_height() {
    babylond status | jq
    systemctl status babylond
}

get_log() {
    sudo journalctl -u babylond.service -f --no-hostname -o cat
}

start_validator_node() {
    read -e -p "请输入你的验证者名称: " validator_name
    sudo tee ~/validator.json > /dev/null <<EOF
{
  "pubkey": $(babylond tendermint show-validator),
  "amount": "1000000ubbn",
  "moniker": "$validator_name",
  "details": "$validator_name validator node",
  "commission-rate": "0.10",
  "commission-max-rate": "0.20",
  "commission-max-change-rate": "0.01",
  "min-self-delegation": "1"
}
EOF
    babylond tx checkpointing create-validator ~/validator.json \
    --chain-id=$CHAIN_ID \
    --gas="auto" \
    --gas-adjustment="1.5" \
    --gas-prices="0.025ubbn" \
    --from=wallet
}

echo && echo -e " ${Red_font_prefix}babylon节点 一键安装脚本${Font_color_suffix} by \033[1;35moooooyoung\033[0m
此脚本完全免费开源, 由推特用户 ${Green_font_prefix}@ouyoung11开发${Font_color_suffix}, 
欢迎关注, 如有收费请勿上当受骗。
 ———————————————————————
 ${Green_font_prefix} 1.安装babylon节点环境 ${Font_color_suffix}
 ${Green_font_prefix} 2.运行babylon节点 ${Font_color_suffix}
 ${Green_font_prefix} 3.检查节点状态 ${Font_color_suffix}
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
