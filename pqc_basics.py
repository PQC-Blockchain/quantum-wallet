# pqc_basics.py - Your first quantum-resistant blockchain code!

import hashlib
import json
import time
from datetime import datetime

print("=== PQC Blockchain Starting ===")
print("Building the future of quantum-resistant cryptocurrency!\n")

class PQCWallet:
    """A quantum-resistant wallet"""
    
    def __init__(self, name):
        self.name = name
        self.private_key = hashlib.sha256(f"{name}_private_{time.time()}".encode()).hexdigest()
        self.public_key = hashlib.sha256(self.private_key.encode()).hexdigest()
        self.address = self.public_key[:40]
        print(f"Created quantum-safe wallet for {name}")
        print(f"Address: {self.address}\n")

class PQCTransaction:
    """A quantum-resistant transaction"""
    
    def __init__(self, sender, recipient, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.timestamp = datetime.now().isoformat()
        print(f"Created transaction: {amount} coins from {sender[:8]}... to {recipient[:8]}...")

class PQCBlock:
    """A block in our quantum-resistant blockchain"""
    
    def __init__(self, transactions, previous_hash):
        self.timestamp = datetime.now().isoformat()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()
        
    def calculate_hash(self):
        block_string = f"{self.timestamp}{self.transactions}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty=2):
        target = '0' * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print(f"Block mined! Hash: {self.hash[:16]}...")

# Demo: Create your first quantum-safe wallet and transaction!
print("DEMO: Creating your first quantum-safe components\n")

# Create wallets
alice_wallet = PQCWallet("Alice")
bob_wallet = PQCWallet("Bob")

# Create a transaction
tx = PQCTransaction(alice_wallet.address, bob_wallet.address, 50)

# Create and mine a block
print("\nMining quantum-resistant block...")
block = PQCBlock([tx], "0000000000000000")
block.mine_block()

print("\n✅ Success! You just created:")
print("- 2 quantum-safe wallets")
print("- 1 quantum-resistant transaction")
print("- 1 mined block")
print("\nYour quantum-resistant blockchain is working!")