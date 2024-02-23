from bitcoinlib.wallets import Wallet, wallet_delete

def generate_addresses(mnemonic, network='testnet', num_addresses=500):
    # Create a new wallet or open an existing one
    wallet_name = 'my_segwit_wallet'
    try:
        wallet_delete(wallet_name)  # Remove existing wallet with the same name, if necessary
    except Exception as e:
        print("No existing wallet to delete, continuing...")
    w = Wallet.create(wallet_name, keys=mnemonic, network=network, witness_type='segwit')

    # Generate addresses
    addresses = []
    for i in range(num_addresses):
        # Instead of using index, we create a new key for each iteration
        key = w.new_key()  # This should generate a new key within the wallet
        addresses.append(key.address)

    # Clean up: remove wallet to avoid clutter
    wallet_delete(wallet_name)
    
    return addresses

def main():
    # Prompt the user for a mnemonic
    mnemonic_input = input("Please enter your mnemonic: ")
    try:
        addresses = generate_addresses(mnemonic_input)
        print("\nGenerated addresses:")
        for i, address in enumerate(addresses):
            print(f"{i + 1}: {address}")
    except Exception as e:
        print("Error during address generation: ", e)

if __name__ == "__main__":
    main()
