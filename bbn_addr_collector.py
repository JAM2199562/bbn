import pexpect
import re

# Function to extract numerical part from the name
def extract_number(name):
    match = re.search(r'\d+$', name)  # This regex finds one or more digits at the end of the string
    return int(match.group()) if match else 0  # Convert found digits to int, default to 0 if no digits

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
command = 'babylond keys list'
keyword = 'lumao'  # The keyword to search in the name

print("Starting command...")  # Debug output
# Start the command and wait for the password prompt
child = pexpect.spawn(command, encoding='utf-8', timeout=30)  # Increase timeout if necessary
try:
    child.expect('Enter keyring passphrase', timeout=10)
    print("Password prompt found, sending password...")  # Debug output
    child.sendline(password)
except pexpect.exceptions.TIMEOUT:
    print("Timeout waiting for password prompt. Check if command requires a password.")
    exit()

# Wait for the end of the command's output
try:
    child.expect(pexpect.EOF)
except pexpect.exceptions.EOF:
    print("Unexpected end of file. Check if command executed properly.")
    exit()
except pexpect.exceptions.TIMEOUT:
    print("Timeout waiting for command to complete. Check if command is taking too long.")
    exit()

output = child.before.strip()  # Get the output
# print(f"Command output:\n{output}")  # Debug output

# Parse the output
pattern = re.compile(r'- address: (\S+)\s+name: (\S+)', re.MULTILINE)
matches = pattern.findall(output)
print(f"Found {len(matches)} entries in the command output.")  # Debug output

# Filter and print names and addresses that contain the keyword
filtered_results = [(name, address) for address, name in matches if keyword in name]
# Sort the filtered_results by the numerical part of the name
filtered_results.sort(key=lambda x: extract_number(x[0]))
if filtered_results:  # Check if there are any filtered results
    for name, address in filtered_results:
        print(f'{name} {address}')
else:
    print("No matching entries found. Check if keyword is correct or present.")  # Debug output

# Close the child process
child.close()
