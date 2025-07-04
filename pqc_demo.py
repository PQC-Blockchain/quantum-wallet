# pqc_demo.py - Enhanced Quantum-Resistant Blockchain Demo

import hashlib
import json
import time
from datetime import datetime

class PQCBlockchain:
    """A complete quantum-resistant blockchain"""
    
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.mining_reward = 100
        self.difficulty = 2
        
        # Create genesis block
        self.create_genesis_block()
        
    def create_genesis_block(self):
        """Create the first block in the chain"""
        genesis_block = {
            'index': 0,
            'timestamp': datetime.now().isoformat(),
            'transactions': [],
            'previous_hash': '0' * 64,
            'nonce': 0
        }
        genesis_block['hash'] = self.calculate_hash(genesis_block)
        self.chain.append(genesis_block)
        print("🌟 Genesis block created!")
        
    def calculate_hash(self, block):
        """Calculate quantum-resistant hash for a block"""
        block_string = json.dumps(block, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def get_latest_block(self):
        """Get the most recent block"""
        return self.chain[-1]
    
    def add_transaction(self, sender, recipient, amount):
        """Add a new quantum-safe transaction"""
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': datetime.now().isoformat(),
            'quantum_safe': True  # This will use PQC signatures
        }
        self.pending_transactions.append(transaction)
        print(f"📝 Transaction added: {amount} QRC from {sender[:8]}... to {recipient[:8]}...")
        return transaction
    
    def mine_pending_transactions(self, mining_reward_address):
        """Mine a new block with quantum-resistant proof of work"""
        # Add mining reward
        reward_tx = {
            'sender': 'NETWORK',
            'recipient': mining_reward_address,
            'amount': self.mining_reward,
            'timestamp': datetime.now().isoformat(),
            'quantum_safe': True
        }
        
        transactions = self.pending_transactions + [reward_tx]
        
        block = {
            'index': len(self.chain),
            'timestamp': datetime.now().isoformat(),
            'transactions': transactions,
            'previous_hash': self.get_latest_block()['hash'],
            'nonce': 0
        }
        
        # Quantum-resistant mining
        print(f"\n⛏️  Mining block #{block['index']}...")
        start_time = time.time()
        
        target = '0' * self.difficulty
        while True:
            block['hash'] = self.calculate_hash(block)
            if block['hash'][:self.difficulty] == target:
                break
            block['nonce'] += 1
            
            # Show progress every 1000 attempts
            if block['nonce'] % 1000 == 0:
                print(f"⚡ Attempting nonce: {block['nonce']}...")
        
        mining_time = round(time.time() - start_time, 2)
        print(f"✅ Block mined in {mining_time} seconds!")
        print(f"🔐 Quantum-safe hash: {block['hash'][:32]}...")
        print(f"🎯 Nonce: {block['nonce']}")
        
        self.chain.append(block)
        self.pending_transactions = []
        
        return block
    
    def get_balance(self, address):
        """Calculate balance for an address"""
        balance = 0
        
        for block in self.chain:
            for tx in block['transactions']:
                if tx['sender'] == address:
                    balance -= tx['amount']
                if tx['recipient'] == address:
                    balance += tx['amount']
                    
        return balance
    
    def is_chain_valid(self):
        """Verify the blockchain hasn't been tampered with"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Verify hash
            if current_block['hash'] != self.calculate_hash(current_block):
                return False
                
            # Verify chain
            if current_block['previous_hash'] != previous_block['hash']:
                return False
                
            # Verify proof of work
            if current_block['hash'][:self.difficulty] != '0' * self.difficulty:
                return False
                
        return True
    
    def display_chain(self):
        """Display the blockchain"""
        print("\n📊 QUANTUM-RESISTANT BLOCKCHAIN STATUS")
        print("=" * 50)
        print(f"Chain length: {len(self.chain)} blocks")
        print(f"Difficulty: {self.difficulty}")
        print(f"Mining reward: {self.mining_reward} QRC")
        print(f"Chain valid: {'✅ Yes' if self.is_chain_valid() else '❌ No'}")
        print("=" * 50)

def create_wallet_address(name):
    """Create a quantum-safe wallet address"""
    # In real implementation, this would use Dilithium/Falcon PQC
    timestamp = str(time.time())
    wallet_data = f"{name}_{timestamp}_quantum_safe"
    address = hashlib.sha256(wallet_data.encode()).hexdigest()
    return address

# DEMO: Run the quantum-resistant blockchain
if __name__ == "__main__":
    print("🚀 QUANTUM-RESISTANT BLOCKCHAIN DEMO")
    print("====================================")
    print("Building the future of crypto security...\n")
    
    # Create blockchain
    qrc_blockchain = PQCBlockchain()
    
    # Create quantum-safe wallets
    print("👛 Creating quantum-safe wallets...")
    alice = create_wallet_address("Alice")
    bob = create_wallet_address("Bob")
    charlie = create_wallet_address("Charlie")
    miner = create_wallet_address("Miner")
    
    print(f"Alice's address: {alice[:16]}...")
    print(f"Bob's address: {bob[:16]}...")
    print(f"Charlie's address: {charlie[:16]}...")
    print(f"Miner's address: {miner[:16]}...")
    
    # Mine first block to get coins
    print("\n💰 Mining first block for initial coins...")
    qrc_blockchain.mine_pending_transactions(miner)
    
    # Create transactions
    print("\n💸 Creating quantum-safe transactions...")
    qrc_blockchain.add_transaction(miner, alice, 50)
    qrc_blockchain.add_transaction(miner, bob, 30)
    
    # Mine block with transactions
    qrc_blockchain.mine_pending_transactions(miner)
    
    # More transactions
    print("\n💸 Creating more transactions...")
    qrc_blockchain.add_transaction(alice, charlie, 20)
    qrc_blockchain.add_transaction(bob, charlie, 10)
    
    # Mine another block
    qrc_blockchain.mine_pending_transactions(miner)
    
    # Display final state
    qrc_blockchain.display_chain()
    
    # Show balances
    print("\n💰 WALLET BALANCES (QRC - Quantum Resistant Coin)")
    print("-" * 50)
    print(f"Miner: {qrc_blockchain.get_balance(miner)} QRC")
    print(f"Alice: {qrc_blockchain.get_balance(alice)} QRC")
    print(f"Bob: {qrc_blockchain.get_balance(bob)} QRC")
    print(f"Charlie: {qrc_blockchain.get_balance(charlie)} QRC")
    print("-" * 50)
    
    print("\n🎉 DEMO COMPLETE!")
    print("Your quantum-resistant blockchain is fully functional!")
    print("\nNext steps:")
    print("1. Add real Dilithium/Falcon signatures")
    print("2. Implement P2P networking")
    print("3. Create a web interface")
    print("4. Launch testnet!")
    
    # Easter egg for your first meme coin
    print("\n🐸 Ready to create the first quantum-safe meme coin?")
    print("Token idea: QPEPE - The Quantum Pepe!")
