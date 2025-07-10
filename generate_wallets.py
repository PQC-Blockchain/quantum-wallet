import json
import secrets
import hashlib

def generate_wallet_address():
    """Generate a QRC wallet address"""
    # Generate random bytes
    random_bytes = secrets.token_bytes(32)
    # Hash them
    hash_object = hashlib.sha256(random_bytes)
    hex_dig = hash_object.hexdigest()
    # Create QRC address
    return f"QRC{hex_dig[:32].upper()}"

def generate_private_key():
    """Generate a private key"""
    return secrets.token_hex(32)

# Generate wallets
wallets = {
    "genesis": {
        "address": generate_wallet_address(),
        "private_key": generate_private_key()
    },
    "mining_rewards": {
        "address": generate_wallet_address(),
        "private_key": generate_private_key()
    },
    "fee_collection": {
        "address": generate_wallet_address(),
        "private_key": generate_private_key()
    },
    "developer_fund": {
        "address": generate_wallet_address(),
        "private_key": generate_private_key()
    }
}

# Save to secure file (DO NOT UPLOAD THIS!)
with open('SENSITIVE_WALLETS.json', 'w') as f:
    json.dump(wallets, f, indent=2)

print("Generated wallets:")
for name, wallet in wallets.items():
    print(f"\n{name}:")
    print(f"  Address: {wallet['address']}")
    print(f"  Private Key: {wallet['private_key']}")

print("\n⚠️  IMPORTANT: Save SENSITIVE_WALLETS.json in a secure location!")
print("Never upload this file to GitHub!")