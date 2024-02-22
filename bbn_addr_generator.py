import pexpect
import time

# Number of addresses to generate
num_addresses = 300  # Change this to modify the number of addresses

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
# Output file for mnemonic phrases
mnemonic_file = 'bbn_mnemonics.txt'

# Main script
with open(mnemonic_file, 'w') as f:
    for i in range(1, num_addresses + 1):
        # Start the process
        child = pexpect.spawn(f'babylond keys add lumao{i}', encoding='utf-8', timeout=120)
        
        # Expecting passphrase input
        child.expect('Enter keyring passphrase')
        child.sendline(passphrase)
        
        # Wait for the process to complete and capture all output
        child.expect(pexpect.EOF)
        
        # Extract all output text
        output = child.before.strip()  # Remove leading/trailing whitespace
        
        # Split the output into lines and find the mnemonic phrase (assuming it's the last line)
        lines = output.split('\n')
        mnemonic = None
        for line in reversed(lines):  # Search from the end
            words = line.split()
            if len(words) == 24:  # Check if the line has 24 words
                mnemonic = line
                break
        
        # Write the mnemonic to the file, if found
        if mnemonic:
            f.write(f'{mnemonic}\n')
            print(f'Address lumao{i} created and mnemonic saved.')
        else:
            print(f'Failed to find mnemonic for lumao{i}.')

        # Make sure to close the child process
        child.close()

        # Optional delay to avoid rate limiting or similar issues
        time.sleep(1)