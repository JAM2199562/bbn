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
    PEERS="e87adbc46473dd0e78fababbdccbf5ac44f00523@159.65.138.163:20656,e80a348f5b1f8128bc6588fedca10ff031d406cb@138.197.171.20:20656,02f4429fba037f09d2be5b3704d97727fc7df1cd@159.203.62.168:20656,641cad695370c18f9d26329cd0bdd0f6c5b25bfb@159.203.20.126:26656,9fafb42160d1a4d656ecd48c59060162b373c1bf@68.183.195.179:26656,7c9bf63c1030ff92878566e779d92b830e572e6c@138.68.47.27:26656,42f7c9bad07c1fa7d02b9ed6c1599f29bfc8a25a@95.217.44.160:45656,d308e89985a5765678995f9a66471386bd093c9e@195.201.111.179:45656,803eb4eeaadce5a1fab1aa69a07cb1775375a240@95.217.37.201:45656,0d4ce1d1158f8707596b812647086b65328d4aaf@95.216.243.99:45656,7a5d702579b64e23b292d277f0395b2a0c59e20b@178.63.173.246:45656,1c8d1f59bf6969b4e386a7be588fac132a0910d9@94.130.200.224:45656,02f4429fba037f09d2be5b3704d97727fc7df1cd@159.203.62.168:20656,19f93d34d257277d7431f638de912a1a1edd1c6b@88.198.62.85:45656,9d9e3501d2e374d65c225e60a5457f5553737300@148.251.238.18:45656,8a3fe0f0433042b700cf231be23780f73b4a5292@144.76.225.220:45656,c5034d8da906a10f42c25d734e181a486999f44b@135.181.136.97:45656,158e5f888dd2e82474be25470793feff2f1fdc17@176.9.30.14:45656,582c99d45f6e992498e08cfc4b5de744d679c89b@138.201.123.167:45656,a1e5faf6ba0606d053954eb1374ea700d090aab8@95.216.241.207:45656,19e80849934bcd0df43a5a033cdca0ea1c614668@95.216.246.110:45656,d60c6a3d22b124a19d89c47d1c1024db35131394@148.251.88.40:45656,29f16adbf23e75c68c5009b6f26b6889e93ff9b7@65.21.76.109:45656,f2788c066a85d8f661d4a6ea3c4122d0e926153e@167.235.72.201:26656,6bcd19ed516694854d1ebe56db3b7a64bb5d3fee@88.198.55.44:45656,e80a348f5b1f8128bc6588fedca10ff031d406cb@138.197.171.20:20656,69be4a00ca3286b830e3d4ece5f7a178e66e14e0@176.9.30.188:45656,286d7f069dc6580ad672fc28dbc957d2a8afd080@95.216.244.142:45656,d8340b6ebca165ef2c400c06b06bacc055f08861@77.248.159.123:26656,7ce7d33cbcc12d77ed5912f6d1f3f4a49add99d1@37.27.97.225:45656,aac6f6c19800c00bb4342de6ca7a32b7c89c715a@95.217.39.119:45656,e82a2166793826ab15d0bbe368c5104148e36693@167.235.185.25:45656,dda6509350274353b124ffd1212444be5c10c5cf@37.60.234.115:20656,40662747f0e01678dbdf1e50879f40a68139d7aa@35.163.58.204:26656,d0893daee4fd97d620a549fe329c71319305d897@95.216.25.29:35656,163f84d88216fcd9003ed65c2b4c019ee410fc4e@47.242.50.51:26656,59790b543de5488c914dfe5e502b1438fcc8ea7a@37.120.189.81:20656,943a2e997f35717052df50524fb245a8df5f417e@95.165.107.241:35656,9fafb42160d1a4d657ecd48c59060162b373c1bf@68.183.195.179:26656,28afb978b6cfd581da4505398fbc755ee83d3858@65.109.30.35:20656,e8be5595046b6d3c427de02fd564211bd7761ef9@75.119.133.94:35656,7c9bf63c1030ff92878566e779d92b830e572e6c@138.68.47.27:26656,67aeeee9d253fc38f4e522bf77bf76386f954fa5@135.181.200.64:26656"
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
