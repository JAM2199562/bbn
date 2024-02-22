import pexpect

# 打开文件并读取所有助记词
with open('bbn_mnemonics.txt', 'r') as file:
    mnemonics = [line.strip() for line in file]

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

# 对每个助记词执行命令
for i, mnemonic in enumerate(mnemonics, start=1):
    child = pexpect.spawn(f'babylond keys delete {i} -y')
    
    # 这里处理密码输入的提示
    child.expect('Enter keyring passphrase \(attempt 1/3\):')
    child.sendline(password)
    
    # 等待所有输出完成
    child.expect(pexpect.EOF)
    
    # 打印命令执行的输出
    print(child.before.decode())  # 假设输出是UTF-8编码，打印输出

# 注意：确保你的密码是正确的，并且考虑到安全性，不要在脚本中硬编码重要的密码。
