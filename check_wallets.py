import requests

# Get blockchain stats
response = requests.get('http://localhost:5000/api/stats')
print(f"Active wallets: {response.json()['active_users']}")

# Create a wallet and immediately test it
print("\nCreating new wallet...")
wallet_response = requests.post('http://localhost:5000/api/wallet/create')
wallet_data = wallet_response.json()
print(f"Created: {wallet_data['address']}")
print(f"Balance: {wallet_data['balance']}")

# Check balance
print("\nChecking balance...")
balance_response = requests.get(f"http://localhost:5000/api/wallet/balance/{wallet_data['address']}")
print(f"Balance check: {balance_response.json()}")

# Try a transaction between API-created wallets
print("\nCreating second wallet...")
wallet2_response = requests.post('http://localhost:5000/api/wallet/create')
wallet2_data = wallet2_response.json()
print(f"Created: {wallet2_data['address']}")

# Send transaction
print("\nSending transaction...")
tx_data = {
    'sender': wallet_data['address'],
    'recipient': wallet2_data['address'],
    'amount': 50,
    'signature': 'test_signature'
}

tx_response = requests.post('http://localhost:5000/api/transaction/send', 
                           json=tx_data)
print(f"Transaction result: {tx_response.json()}")
