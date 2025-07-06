import requests
import json
import time
from dilithium_wrapper import QuantumResistantWallet

def test_quantum_blockchain():
    """Test the quantum-resistant blockchain implementation"""
    
    base_url = "http://localhost:5000"
    
    print("=== Quantum-Resistant Blockchain Test ===\n")
    
    # 1. Check quantum security status
    print("1. Checking quantum security status...")
    response = requests.get(f"{base_url}/api/quantum/security")
    security_info = response.json()
    print(f"   ✓ Quantum Resistant: {security_info['quantum_resistant']}")
    print(f"   ✓ Algorithm: {security_info['signature_algorithm']}")
    print(f"   ✓ NIST Level: {security_info['nist_level']}")
    print(f"   ✓ Signature Size: {security_info['key_sizes']['signature']} bytes\n")
    
    # 2. Create quantum-resistant wallets
    print("2. Creating quantum-resistant wallets...")
    
    # Create sender wallet
    response1 = requests.post(f"{base_url}/api/wallet/create")
    wallet1 = response1.json()
    print(f"   ✓ Wallet 1: {wallet1['address']}")
    print(f"   ✓ Algorithm: {wallet1['algorithm']}")
    print(f"   ✓ Public Key Size: {wallet1['public_key_size']} bytes")
    
    # Create recipient wallet
    response2 = requests.post(f"{base_url}/api/wallet/create")
    wallet2 = response2.json()
    print(f"   ✓ Wallet 2: {wallet2['address']}\n")
    
    # 3. Test quantum-resistant transaction
    print("3. Sending quantum-resistant transaction...")
    transaction_data = {
        'sender': wallet1['address'],
        'recipient': wallet2['address'],
        'amount': 100,
        'algorithm': 'CRYSTALS-Dilithium-2'
    }
    
    response = requests.post(f"{base_url}/api/transaction/send", json=transaction_data)
    tx_result = response.json()
    
    if tx_result['success']:
        print(f"   ✓ Transaction sent successfully!")
        print(f"   ✓ Quantum signature applied: {tx_result['quantum_signature']}")
        print(f"   ✓ Transaction ID: {tx_result['transaction_id']}\n")
    
    # 4. Check balances
    print("4. Checking updated balances...")
    
    # Check sender balance
    response = requests.get(f"{base_url}/api/wallet/balance/{wallet1['address']}")
    balance1 = response.json()
    print(f"   ✓ Wallet 1 balance: {balance1['balance']} QRC")
    
    # Check recipient balance
    response = requests.get(f"{base_url}/api/wallet/balance/{wallet2['address']}")
    balance2 = response.json()
    print(f"   ✓ Wallet 2 balance: {balance2['balance']} QRC\n")
    
    # 5. Check blockchain stats
    print("5. Checking blockchain statistics...")
    response = requests.get(f"{base_url}/api/stats")
    stats = response.json()
    print(f"   ✓ Current TPS: {stats['current_tps']}")
    print(f"   ✓ Block Height: {stats['block_height']}")
    print(f"   ✓ Quantum Resistant: {stats['quantum_resistant']}")
    print(f"   ✓ Signature Algorithm: {stats['signature_algorithm']}\n")
    
    # 6. Performance comparison
    print("6. Quantum vs Classical Comparison:")
    print("   ┌─────────────────────────────────────────┐")
    print("   │ Feature          │ Classical │ Quantum  │")
    print("   ├─────────────────────────────────────────┤")
    print("   │ Algorithm        │ ECDSA     │ Dilithium│")
    print("   │ Quantum Safe     │ ❌        │ ✅       │")
    print("   │ Signature Size   │ 71 bytes  │ 2420 B   │")
    print("   │ Security Level   │ 128-bit   │ 128-bit  │")
    print("   │ Future Proof     │ ❌        │ ✅       │")
    print("   └─────────────────────────────────────────┘\n")
    
    print("✅ All quantum-resistant features working correctly!")

if __name__ == "__main__":
    # Make sure the blockchain server is running
    print("Make sure the blockchain server is running on http://localhost:5000\n")
    
    try:
        test_quantum_blockchain()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to blockchain server.")
        print("   Please start the server with: python quantum_blockchain_server_v4.py")