import subprocess
import csv

def run_command_and_capture_output(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, text=True)
    output_lines = []

    # 逐行读取输出
    while True:
        line = process.stdout.readline()
        if not line:
            break
        output_lines.append(line.strip())

    return output_lines

def extract_address(output_lines):
    for line in output_lines:
        if line.startswith('- address: '):
            return line.split('address: ')[1]
    return None

def main():
    wallets = []

    for i in range(1, 21):
        command = f'babylond keys add lumao{i}'
        output_lines = run_command_and_capture_output(command)
        address = extract_address(output_lines)

        if address:
            wallets.append({'name': f'lumao{i}', 'address': address})
            print(f"Wallet 'lumao{i}': Address: {address}\n")
            print("--------------------------------------------------\n")  # 分隔符

    # 将地址保存到CSV文件
    with open('wallets.csv', 'w', newline='') as csvfile:
        fieldnames = ['name', 'address']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for wallet in wallets:
            writer.writerow(wallet)

if __name__ == '__main__':
    main()

