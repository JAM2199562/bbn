rm -rf $HOME/.babylond
rm -rf $HOME/babylon
rm -rf $HOME/go
systemctl stop babylon
systemctl stop babylond
rm -rf /etc/systemd/system/babylon.service
rm -rf /etc/systemd/system/babylond.service

