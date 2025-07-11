# fee_manager.py
import json
import time
from decimal import Decimal, ROUND_DOWN
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FeeManager:
    """Manages all fee calculations and distributions for PQC Blockchain"""
    
    def __init__(self):
        # Get addresses from environment
        self.developer_address = os.getenv('PQC_DEVELOPER_ADDRESS')
        self.treasury_address = os.getenv('PQC_TREASURY_ADDRESS')
        
        if not self.developer_address or not self.treasury_address:
            raise ValueError(
                "Please set PQC_DEVELOPER_ADDRESS and PQC_TREASURY_ADDRESS in .env file\n"
                "Example:\n"
                "PQC_DEVELOPER_ADDRESS=your_developer_wallet_address\n"
                "PQC_TREASURY_ADDRESS=your_treasury_wallet_address"
            )
        
        # Your fee configuration
        self.fees = {
            "transaction_fee_percentage": Decimal("0.0005"),  # 0.05%
            "minimum_fee": Decimal("0.00005"),
            "developer_fee_percentage": Decimal("0.00025"),   # 0.025% (50% of transaction fee)
            "features": {
                "token_creation_fee": Decimal("25"),
                "name_registration_fee": Decimal("2.5"),
                "storage_fee_per_mb": Decimal("0.5")
            }
        }
        
        print(f"✓ Fee Manager initialized")
        print(f"  Developer address: {self.developer_address[:10]}...")
        print(f"  Treasury address: {self.treasury_address[:10]}...")
    
    def calculate_transaction_fee(self, amount):
        """Calculate fee for regular transaction"""
        amount = Decimal(str(amount))
        
        # Calculate percentage-based fee
        percentage_fee = amount * self.fees["transaction_fee_percentage"]
        
        # Apply minimum fee if necessary
        total_fee = max(percentage_fee, self.fees["minimum_fee"])
        
        # Split between network and developer
        developer_share = total_fee * (self.fees["developer_fee_percentage"] / self.fees["transaction_fee_percentage"])
        network_share = total_fee - developer_share
        
        return {
            "total_fee": float(total_fee.quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)),
            "developer_fee": float(developer_share.quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)),
            "network_fee": float(network_share.quantize(Decimal("0.00000001"), rounding=ROUND_DOWN))
        }
    
    def create_fee_transactions(self, sender, amount, signature, timestamp):
        """Create the actual fee distribution transactions"""
        fees = self.calculate_transaction_fee(amount)
        
        fee_transactions = []
        
        # Developer fee transaction
        if fees["developer_fee"] > 0:
            fee_transactions.append({
                "sender": sender,
                "recipient": self.developer_address,
                "amount": fees["developer_fee"],
                "timestamp": timestamp + 0.001,  # Slightly after main transaction
                "type": "developer_fee",
                "signature": signature  # Same signature validates fee payment
            })
        
        # Network fee transaction
        if fees["network_fee"] > 0:
            fee_transactions.append({
                "sender": sender,
                "recipient": self.treasury_address,
                "amount": fees["network_fee"],
                "timestamp": timestamp + 0.002,  # Slightly after developer fee
                "type": "network_fee",
                "signature": signature
            })
        
        return fee_transactions, fees
    
    def calculate_feature_fee(self, feature_type, **kwargs):
        """Calculate fee for blockchain features (tokens, names, storage)"""
        if feature_type == "token_creation":
            total_fee = float(self.fees["features"]["token_creation_fee"])
        elif feature_type == "name_registration":
            total_fee = float(self.fees["features"]["name_registration_fee"])
        elif feature_type == "storage":
            size_mb = kwargs.get('size_mb', 1)
            total_fee = float(self.fees["features"]["storage_fee_per_mb"] * Decimal(str(size_mb)))
        else:
            total_fee = 0
            
        return {
            "total_fee": total_fee,
            "developer_fee": total_fee,  # 100% goes to developer for features
            "network_fee": 0,
            "fee_transactions": [
                {
                    "recipient": self.developer_address,
                    "amount": total_fee,
                    "type": f"{feature_type}_fee"
                }
            ]
        }
    
    def create_fee_distribution_transactions(self, main_transaction, fee_structure):
        """Create fee distribution transactions for features"""
        fee_transactions = []
        timestamp = main_transaction.get('timestamp', time.time())
        
        for i, fee_tx in enumerate(fee_structure.get('fee_transactions', [])):
            fee_transactions.append({
                "sender": main_transaction['sender'],
                "recipient": fee_tx['recipient'],
                "amount": fee_tx['amount'],
                "timestamp": timestamp + (0.001 * (i + 1)),
                "type": fee_tx['type'],
                "signature": main_transaction.get('signature', ''),
                "quantum_resistant": True
            })
            
        return fee_transactions