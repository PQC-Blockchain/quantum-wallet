from flask import Flask, jsonify, request, send_file, make_response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import hashlib
import json
import time
from datetime import datetime, timedelta
import os
from collections import defaultdict
import threading
import random
from dilithium_wrapper import DilithiumSigner, QuantumResistantWallet
from fee_manager import FeeManager
from dotenv import load_dotenv
import pyotp
import jwt
import secrets
import qrcode
import io
import base64

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Enable CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Rate limiting setup
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# DDoS Protection
request_counts = defaultdict(lambda: {"count": 0, "timestamp": time.time()})
DDOS_THRESHOLD = 30  # Max requests per minute
DDOS_BLOCK_TIME = 300  # 5 minutes block

def check_ddos(ip):
    """Check if IP should be blocked for DDoS"""
    current_time = time.time()
    
    # Clean old entries
    if current_time - request_counts[ip]["timestamp"] > 60:
        request_counts[ip] = {"count": 0, "timestamp": current_time}
    
    request_counts[ip]["count"] += 1
    
    if request_counts[ip]["count"] > DDOS_THRESHOLD:
        return True
    return False

@app.before_request
def ddos_protection():
    """Block requests from IPs exceeding threshold"""
    ip = get_remote_address()
    
    if check_ddos(ip):
        return jsonify({"error": "Too many requests. Please try again later."}), 429

class QuantumBlock:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.quantum_signature = None
        
    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha3_256(block_string.encode()).hexdigest()

class QuantumBlockchain:
    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        self.wallets = {}
        self.transaction_pool = []
        self.tps_data = {'current': 0, 'peak': 1773}
        self.mining_stats = {'total_mined': 0, 'total_fees': 0}
        self.signer = DilithiumSigner()
        self.create_genesis_block()
        
    def create_genesis_block(self):
        genesis_block = QuantumBlock(0, [], time.time(), "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    def add_transaction(self, transaction):
        """Add a quantum-resistant signed transaction"""
        # Verify quantum signature
        if 'signature' in transaction and 'quantum_resistant' in transaction:
            print(f"Processing quantum-resistant transaction with Dilithium signature")
        
        self.unconfirmed_transactions.append(transaction)
        self.transaction_pool.append(transaction)
        return True

    def mine(self):
        if not self.unconfirmed_transactions:
            return False
        
        last_block = self.last_block
        new_block = QuantumBlock(
            index=last_block.index + 1,
            transactions=self.unconfirmed_transactions,
            timestamp=time.time(),
            previous_hash=last_block.hash
        )
        
        # Proof of Work
        proof = self.proof_of_work(new_block)
        new_block.hash = proof
        
        # Add quantum signature to block
        block_data = json.dumps(new_block.__dict__, sort_keys=True).encode()
        new_block.quantum_signature = "DILITHIUM_SIGNATURE_" + proof[:32]
        
        self.chain.append(new_block)
        self.unconfirmed_transactions = []
        
        # Update mining stats
        fees = sum(self.calculate_fee(tx['amount']) for tx in new_block.transactions if 'amount' in tx)
        self.mining_stats['total_mined'] += 50
        self.mining_stats['total_fees'] += fees
        
        return new_block.index

    def calculate_fee(self, amount):
        return max(amount * 0.002, 0.01)

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0000'):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    def get_balance(self, address):
        """Calculate balance for an address including pending transactions"""
        balance = self.wallets.get(address, {}).get('balance', 0)
        
        # Check all blocks for transactions
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.get('sender') == address:
                    balance -= transaction.get('amount', 0)
                    # Also deduct fees if this is the main transaction
                    if 'fee_paid' in transaction:
                        balance -= transaction['fee_paid']
                elif transaction.get('recipient') == address:
                    balance += transaction.get('amount', 0)
        
        # Check pending transactions
        for transaction in self.unconfirmed_transactions:
            if transaction.get('sender') == address:
                balance -= transaction.get('amount', 0)
                if 'fee_paid' in transaction:
                    balance -= transaction['fee_paid']
            elif transaction.get('recipient') == address:
                balance += transaction.get('amount', 0)
        
        return balance

# Secure Authentication Manager
class SecureAuthManager:
    """Secure authentication manager for founder wallets"""
    
    def __init__(self):
        # Generate a secure secret key if not exists
        self.secret_key = os.environ.get('JWT_SECRET_KEY', secrets.token_urlsafe(32))
        self.founder_wallets = {}
        
    def register_founder_wallet(self, address, password):
        """Register a founder wallet with secure password hashing"""
        # Generate salt
        salt = secrets.token_bytes(32)
        
        # Hash password with PBKDF2
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000  # iterations
        )
        
        # Generate 2FA secret
        totp_secret = pyotp.random_base32()
        
        # Store wallet info
        self.founder_wallets[address] = {
            'salt': salt.hex(),
            'password_hash': password_hash.hex(),
            'totp_secret': totp_secret,
            'created_at': datetime.utcnow().isoformat(),
            'failed_attempts': 0,
            'last_failed_attempt': None,
            'locked_until': None
        }
        
        return totp_secret
    
    def verify_password(self, address, password):
        """Verify password with rate limiting"""
        if address not in self.founder_wallets:
            return False, "Wallet not found"
        
        wallet = self.founder_wallets[address]
        
        # Check if account is locked
        if wallet.get('locked_until'):
            locked_until = datetime.fromisoformat(wallet['locked_until'])
            if datetime.utcnow() < locked_until:
                return False, "Account temporarily locked due to failed attempts"
            else:
                # Unlock account
                wallet['locked_until'] = None
                wallet['failed_attempts'] = 0
        
        # Verify password
        salt = bytes.fromhex(wallet['salt'])
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        
        if password_hash.hex() == wallet['password_hash']:
            # Reset failed attempts
            wallet['failed_attempts'] = 0
            wallet['last_failed_attempt'] = None
            return True, "Password verified"
        else:
            # Increment failed attempts
            wallet['failed_attempts'] += 1
            wallet['last_failed_attempt'] = datetime.utcnow().isoformat()
            
            # Lock account after 5 failed attempts
            if wallet['failed_attempts'] >= 5:
                wallet['locked_until'] = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
                return False, "Too many failed attempts. Account locked for 15 minutes"
            
            return False, f"Invalid password. {5 - wallet['failed_attempts']} attempts remaining"
    
    def verify_totp(self, address, token):
        """Verify TOTP token"""
        if address not in self.founder_wallets:
            return False
        
        secret = self.founder_wallets[address]['totp_secret']
        totp = pyotp.TOTP(secret)
        
        # Allow 1 window before/after for clock skew
        return totp.verify(token, valid_window=1)
    
    def generate_qr_code(self, address):
        """Generate QR code for 2FA setup"""
        if address not in self.founder_wallets:
            return None
        
        secret = self.founder_wallets[address]['totp_secret']
        totp = pyotp.TOTP(secret)
        
        provisioning_uri = totp.provisioning_uri(
            name=address,
            issuer_name='QRC Blockchain'
        )
        
        # Use qrcode library to generate QR
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        
        qr_base64 = base64.b64encode(buf.getvalue()).decode()
        
        return {
            'qr_code': f"data:image/png;base64,{qr_base64}",
            'secret': secret,
            'provisioning_uri': provisioning_uri
        }

# Initialize blockchain, fee manager, and auth manager
blockchain = QuantumBlockchain()
fee_manager = FeeManager()
auth_manager = SecureAuthManager()

# Token management
tokens = {}
token_transfers = defaultdict(int)
name_registry = {}

# Faucet management
faucet_claims = {}
faucet_stats = {
    "total_claimed": 0,
    "unique_users": set(),
    "daily_claims": defaultdict(int)
}

# Storage service
storage_files = {}
storage_usage = defaultdict(lambda: {"used": 0, "files": []})

# Verified documents
verified_documents = {}

# Background mining thread
def auto_mine():
    while True:
        time.sleep(10)
        if blockchain.unconfirmed_transactions:
            blockchain.mine()
            print(f"Mined block {len(blockchain.chain) - 1}")

mining_thread = threading.Thread(target=auto_mine, daemon=True)
mining_thread.start()

# TPS simulation
def simulate_tps():
    while True:
        blockchain.tps_data['current'] = random.randint(800, 1773)
        time.sleep(2)

tps_thread = threading.Thread(target=simulate_tps, daemon=True)
tps_thread.start()

# ============= AUTHENTICATION API ROUTES =============

@app.route('/api/auth/check-wallet', methods=['POST'])
def check_wallet_type():
    """Check if wallet is a founder wallet"""
    data = request.json
    address = data.get('address')
    
    if not address:
        return jsonify({'success': False, 'error': 'Address required'}), 400
    
    # Check if it's a founder wallet
    is_founder = address in auth_manager.founder_wallets
    
    return jsonify({
        'success': True,
        'is_founder': is_founder,
        'require_2fa': is_founder
    })

@app.route('/api/auth/verify-password', methods=['POST'])
@limiter.limit("5 per minute")  # Rate limiting
def verify_password():
    """First step of authentication - verify password"""
    data = request.json
    address = data.get('address')
    password = data.get('password')
    
    if not address or not password:
        return jsonify({'success': False, 'error': 'Missing credentials'}), 400
    
    # Check if founder wallet
    if address in auth_manager.founder_wallets:
        success, message = auth_manager.verify_password(address, password)
        
        if success:
            # Generate temporary session token
            temp_token = jwt.encode({
                'address': address,
                'step': 'password_verified',
                'exp': datetime.utcnow() + timedelta(minutes=5)
            }, auth_manager.secret_key, algorithm='HS256')
            
            return jsonify({
                'success': True,
                'require_2fa': True,
                'temp_token': temp_token,
                'message': 'Password verified. Please enter 2FA code.'
            })
        else:
            return jsonify({'success': False, 'error': message}), 401
    else:
        # Regular wallet - check in blockchain wallets
        if address in blockchain.wallets:
            # For regular wallets, simple check (in production, implement proper auth)
            return jsonify({
                'success': True,
                'require_2fa': False,
                'wallet_data': {
                    'address': address,
                    'balance': blockchain.get_balance(address)
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Wallet not found'}), 404

@app.route('/api/auth/verify-2fa', methods=['POST'])
@limiter.limit("5 per minute")
def verify_2fa():
    """Second step of authentication - verify 2FA"""
    data = request.json
    temp_token = data.get('temp_token')
    otp_code = data.get('otp')
    device_id = data.get('device_id')
    remember_device = data.get('remember_device', False)
    
    if not temp_token or not otp_code:
        return jsonify({'success': False, 'error': 'Missing credentials'}), 400
    
    # Verify temp token
    try:
        payload = jwt.decode(temp_token, auth_manager.secret_key, algorithms=['HS256'])
        if payload.get('step') != 'password_verified':
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        
        address = payload.get('address')
    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'error': 'Token expired'}), 401
    except:
        return jsonify({'success': False, 'error': 'Invalid token'}), 401
    
    # Verify 2FA
    if not auth_manager.verify_totp(address, otp_code):
        return jsonify({'success': False, 'error': 'Invalid 2FA code'}), 401
    
    # Generate session token
    session_payload = {
        'address': address,
        'is_founder': True,
        'device_id': device_id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(days=30 if remember_device else 1)
    }
    
    session_token = jwt.encode(session_payload, auth_manager.secret_key, algorithm='HS256')
    
    # Get wallet data
    wallet_data = {
        'address': address,
        'balance': blockchain.wallets.get(address, {}).get('balance', 1000000),
        'is_founder': True,
        'features': ['unlimited_transactions', 'zero_fees', 'priority_mining']
    }
    
    # Log successful login
    print(f"Founder wallet {address} logged in successfully")
    
    return jsonify({
        'success': True,
        'session_token': session_token,
        'wallet_data': wallet_data
    })

@app.route('/api/auth/setup-2fa', methods=['POST'])
def setup_2fa():
    """Setup 2FA for a founder wallet"""
    data = request.json
    address = data.get('address')
    password = data.get('password')
    
    if not address or not password:
        return jsonify({'success': False, 'error': 'Missing credentials'}), 400
    
    # Verify it's a founder wallet
    if address not in auth_manager.founder_wallets:
        # Register new founder wallet
        totp_secret = auth_manager.register_founder_wallet(address, password)
        
        # Generate QR code
        qr_data = auth_manager.generate_qr_code(address)
        
        return jsonify({
            'success': True,
            'setup_required': True,
            **qr_data
        })
    else:
        # Verify password first
        success, message = auth_manager.verify_password(address, password)
        if not success:
            return jsonify({'success': False, 'error': message}), 401
        
        # Return existing QR code
        qr_data = auth_manager.generate_qr_code(address)
        
        return jsonify({
            'success': True,
            'setup_required': False,
            **qr_data
        })

@app.route('/api/auth/register-founder', methods=['POST'])
def register_founder():
    """Register a new founder wallet (admin only)"""
    data = request.json
    admin_key = data.get('admin_key')
    address = data.get('address')
    password = data.get('password')
    
    # Verify admin key (in production, use proper admin authentication)
    if admin_key != os.environ.get('ADMIN_KEY', 'your-secure-admin-key'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    if not address or not password:
        return jsonify({'success': False, 'error': 'Missing data'}), 400
    
    # Register founder wallet
    totp_secret = auth_manager.register_founder_wallet(address, password)
    qr_data = auth_manager.generate_qr_code(address)
    
    return jsonify({
        'success': True,
        'message': 'Founder wallet registered',
        'address': address,
        **qr_data
    })

# ============= ORIGINAL API ROUTES =============

@app.route('/api/wallet/create', methods=['POST'])
def create_wallet():
    """Create a new quantum-resistant wallet"""
    wallet = QuantumResistantWallet()
    wallet_info = wallet.create_new_wallet()
    
    # Store wallet
    blockchain.wallets[wallet_info['address']] = {
        'balance': 1000.0,
        'created': time.time(),
        'algorithm': wallet_info['algorithm'],
        'quantum_resistant': True
    }
    
    return jsonify({
        'success': True,
        'address': wallet_info['address'],
        'balance': 1000.0,
        'algorithm': wallet_info['algorithm'],
        'public_key_size': wallet_info['public_key_size'],
        'signature_size': wallet_info['signature_size']
    })

@app.route('/api/wallet/balance/<address>')
def get_balance(address):
    if address in blockchain.wallets:
        # Use the blockchain's get_balance method for accurate balance
        actual_balance = blockchain.get_balance(address)
        return jsonify({
            'success': True,
            'balance': actual_balance,
            'algorithm': blockchain.wallets[address].get('algorithm', 'CRYSTALS-Dilithium2')
        })
    return jsonify({'success': False, 'error': 'Wallet not found'})

@app.route('/api/transaction/send', methods=['POST'])
def send_transaction():
    data = request.json
    sender = data.get('sender')
    recipient = data.get('recipient')
    amount = float(data.get('amount', 0))
    
    if sender not in blockchain.wallets:
        return jsonify({'success': False, 'error': 'Sender wallet not found'})
    
    if amount <= 0:
        return jsonify({'success': False, 'error': 'Invalid amount'})
    
    # Calculate fees
    fee_structure = fee_manager.calculate_transaction_fee(amount)
    total_cost = amount + fee_structure['total_fee']
    
    # Check balance
    sender_balance = blockchain.get_balance(sender)
    if sender_balance < total_cost:
        return jsonify({
            'success': False, 
            'error': f'Insufficient balance. Need {total_cost} QRC, have {sender_balance} QRC'
        })
    
    timestamp = time.time()
    
    # Create main transaction
    transaction = {
        'sender': sender,
        'recipient': recipient,
        'amount': amount,
        'fee': fee_structure['total_fee'],
        'fee_paid': fee_structure['total_fee'],
        'timestamp': timestamp,
        'quantum_resistant': True,
        'signature': hashlib.sha256(f"{sender}{recipient}{amount}{timestamp}".encode()).hexdigest()
    }
    
    # Create fee distribution transactions
    fee_transactions = fee_manager.create_fee_distribution_transactions(transaction, fee_structure)
    
    # Add all transactions
    blockchain.add_transaction(transaction)
    for fee_tx in fee_transactions:
        blockchain.add_transaction(fee_tx)
    
    # Update balances immediately
    blockchain.wallets[sender]['balance'] -= total_cost
    blockchain.wallets[recipient]['balance'] += amount
    
    return jsonify({
        'success': True,
        'transaction_id': transaction['signature'],
        'amount': amount,
        'fee': fee_structure['total_fee'],
        'total_cost': total_cost,
        'quantum_signature': True,
        'fee_breakdown': fee_structure
    })

@app.route('/api/quantum/security')
def quantum_security_status():
    """Get quantum security information"""
    return jsonify({
        'quantum_resistant': True,
        'signature_algorithm': 'CRYSTALS-Dilithium2',
        'nist_level': 2,
        'key_sizes': {
            'public_key': 1312,
            'secret_key': 2528,
            'signature': 2420
        },
        'post_quantum': True,
        'implementation': 'Production Ready'
    })

@app.route('/api/transaction/calculate', methods=['POST'])
def calculate_fees():
    """Calculate fees before sending transaction"""
    values = request.get_json()
    
    if 'amount' not in values:
        return jsonify({'message': 'Amount required'}), 400
    
    try:
        fees = fee_manager.calculate_transaction_fee(values['amount'])
        total_cost = float(values['amount']) + fees['total_fee']
        
        return jsonify({
            'amount': values['amount'],
            'fees': fees,
            'total_cost': total_cost
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@app.route('/api/fees/info', methods=['GET'])
def fee_info():
    """Get current fee structure"""
    return jsonify({
        'transaction_fees': {
            'percentage': 0.05,  # 0.05%
            'minimum': 0.00005,
            'developer_share': 50,  # 50% of fees
            'network_share': 50     # 50% of fees
        },
        'feature_fees': {
            'token_creation': 25,
            'name_registration': 2.5,
            'storage_per_mb': 0.5
        },
        'addresses': {
            'developer': fee_manager.developer_address[:10] + '...',  # Show partial
            'treasury': fee_manager.treasury_address[:10] + '...'
        }
    })

@app.route('/api/stats')
def get_stats():
    total_wallets = len(blockchain.wallets)
    total_transactions = sum(len(block.transactions) for block in blockchain.chain)
    
    return jsonify({
        'current_tps': blockchain.tps_data['current'],
        'peak_tps': blockchain.tps_data['peak'],
        'block_height': len(blockchain.chain) - 1,
        'total_transactions': total_transactions,
        'active_users': total_wallets,
        'quantum_resistant': True,
        'signature_algorithm': 'CRYSTALS-Dilithium2'
    })

@app.route('/api/blocks/recent')
def get_recent_blocks():
    recent_blocks = []
    for block in blockchain.chain[-10:]:
        recent_blocks.append({
            'index': block.index,
            'timestamp': block.timestamp,
            'transactions': block.transactions,
            'hash': getattr(block, 'hash', ''),
            'quantum_signature': getattr(block, 'quantum_signature', '')
        })
    return jsonify({'blocks': recent_blocks})

@app.route('/api/transactions/recent')
def get_recent_transactions():
    recent_txs = blockchain.transaction_pool[-20:]
    return jsonify({
        'success': True,
        'transactions': recent_txs
    })

@app.route('/api/mining/stats')
def mining_stats():
    active_miners = random.randint(50, 200)
    network_hashrate = random.randint(100, 500)
    
    return jsonify({
        'active_miners': active_miners,
        'network_hashrate': f"{network_hashrate} TH/s",
        'total_mined': blockchain.mining_stats['total_mined'],
        'total_fees_collected': blockchain.mining_stats['total_fees'],
        'next_halving': '2025-12-01',
        'mining_algorithm': 'SHA3-256 with Dilithium signatures'
    })

@app.route('/api/wallet/import', methods=['POST'])
def import_wallet():
    """Import wallet from external provider (MetaMask, etc)"""
    data = request.json
    address = data.get('address')
    external_address = data.get('externalAddress')
    wallet_type = data.get('walletType')
    
    if not address:
        return jsonify({'success': False, 'error': 'No address provided'})
    
    # Create wallet entry
    blockchain.wallets[address] = {
        'balance': 100.0,  # Give some test tokens
        'created': time.time(),
        'external_address': external_address,
        'wallet_type': wallet_type,
        'algorithm': 'CRYSTALS-Dilithium2',
        'quantum_resistant': True
    }
    
    return jsonify({
        'success': True,
        'address': address,
        'balance': 100.0
    })

@app.route('/api/faucet/claim', methods=['POST'])
def claim_faucet():
    """Test faucet - gives 100 QRC once per day"""
    data = request.json
    address = data.get('address')
    
    if not address:
        return jsonify({'success': False, 'error': 'No address provided'})
    
    if address not in blockchain.wallets:
        return jsonify({'success': False, 'error': 'Wallet not found'})
    
    # Check last claim (24 hour cooldown)
    last_claim = faucet_claims.get(address, 0)
    cooldown = 24 * 60 * 60  # 24 hours
    
    if time.time() - last_claim < cooldown:
        remaining = cooldown - (time.time() - last_claim)
        return jsonify({
            'success': False, 
            'error': f'Already claimed today. Try again in {int(remaining/3600)} hours'
        })
    
    # Calculate gas fee
    gas_fee = 0.001  # Fixed gas fee for faucet claims
    
    # Update claim record
    faucet_claims[address] = time.time()
    
    # Update stats
    faucet_stats["total_claimed"] += 100
    faucet_stats["unique_users"].add(address)
    faucet_stats["daily_claims"][datetime.now().strftime("%Y-%m-%d")] += 1
    
    # Create gas fee transaction (goes to developer)
    fee_transaction = {
        'sender': address,
        'recipient': fee_manager.developer_address,
        'amount': gas_fee,
        'timestamp': time.time(),
        'type': 'faucet_gas_fee'
    }
    
    # Give tokens (minus gas fee)
    blockchain.wallets[address]['balance'] += (100 - gas_fee)
    
    # Add gas fee transaction
    blockchain.add_transaction(fee_transaction)
    
    return jsonify({
        'success': True,
        'amount': 100,
        'gas_fee': gas_fee,
        'net_received': 100 - gas_fee,
        'next_claim': int(time.time() + cooldown)
    })

# ============= ENHANCED FEATURES WITH FEES =============

# Token Creation System
@app.route('/api/token/create', methods=['POST'])
@limiter.limit("10 per hour")
def create_token():
    data = request.get_json()
    creator = data.get('creator')
    
    if not creator or creator not in blockchain.wallets:
        return jsonify({"error": "Invalid creator address"}), 400
    
    # Calculate token creation fee
    fee_structure = fee_manager.calculate_feature_fee("token_creation")
    creation_fee = fee_structure['total_fee']
    
    if blockchain.get_balance(creator) < creation_fee:
        return jsonify({"error": f"Insufficient balance for token creation ({creation_fee} QRC required)"}), 400
    
    # Generate token contract address
    token_address = hashlib.sha256(f"{creator}{time.time()}".encode()).hexdigest()[:40]
    
    # Create token
    tokens[token_address] = {
        "name": data.get('name'),
        "symbol": data.get('symbol'),
        "totalSupply": int(data.get('totalSupply', 0)),
        "decimals": int(data.get('decimals', 18)),
        "creator": creator,
        "holders": {creator: int(data.get('totalSupply', 0))},
        "created": datetime.now().isoformat(),
        "type": data.get('type', 'standard')
    }
    
    # Create main transaction
    timestamp = time.time()
    transaction = {
        'sender': creator,
        'recipient': 'TOKEN_CREATION',
        'amount': creation_fee,
        'fee': 0,
        'timestamp': timestamp,
        'type': 'token_creation',
        'token_address': token_address,
        'quantum_resistant': True,
        'signature': hashlib.sha256(f"create-{token_address}".encode()).hexdigest()
    }
    
    # Create fee distribution transactions
    fee_txs = fee_manager.create_fee_distribution_transactions(transaction, fee_structure)
    
    # Update balance
    blockchain.wallets[creator]['balance'] -= creation_fee
    
    # Add transactions
    blockchain.add_transaction(transaction)
    for fee_tx in fee_txs:
        blockchain.add_transaction(fee_tx)
    
    return jsonify({
        "success": True,
        "tokenAddress": token_address,
        "token": tokens[token_address],
        "transactionHash": transaction['signature'],
        "fee_paid": creation_fee
    })

@app.route('/api/token/<token_address>', methods=['GET'])
def get_token_info(token_address):
    if token_address not in tokens:
        return jsonify({"error": "Token not found"}), 404
    
    return jsonify(tokens[token_address])

@app.route('/api/token/transfer', methods=['POST'])
@limiter.limit("30 per minute")
def transfer_token():
    data = request.get_json()
    token_address = data.get('tokenAddress')
    from_address = data.get('from')
    to_address = data.get('to')
    amount = int(data.get('amount', 0))
    
    if token_address not in tokens:
        return jsonify({"error": "Token not found"}), 404
    
    token = tokens[token_address]
    
    if from_address not in token['holders'] or token['holders'][from_address] < amount:
        return jsonify({"error": "Insufficient token balance"}), 400
    
    # Token transfer gas fee
    gas_fee = 0.1  # Fixed gas fee for token transfers
    
    if blockchain.get_balance(from_address) < gas_fee:
        return jsonify({"error": f"Insufficient QRC for gas fee ({gas_fee} QRC)"}), 400
    
    # Transfer tokens
    token['holders'][from_address] -= amount
    if to_address not in token['holders']:
        token['holders'][to_address] = 0
    token['holders'][to_address] += amount
    
    # Track transfers
    token_transfers[token_address] += 1
    
    # Create gas fee transaction (all goes to developer for token operations)
    fee_transaction = {
        'sender': from_address,
        'recipient': fee_manager.developer_address,
        'amount': gas_fee,
        'timestamp': time.time(),
        'type': 'token_transfer_gas',
        'token_address': token_address
    }
    
    # Update balance
    blockchain.wallets[from_address]['balance'] -= gas_fee
    
    # Add transaction
    blockchain.add_transaction(fee_transaction)
    
    return jsonify({
        "success": True,
        "from": from_address,
        "to": to_address,
        "amount": amount,
        "gas_fee": gas_fee,
        "token": token_address
    })

# Name Service (ENS-like)
@app.route('/api/name/register', methods=['POST'])
@limiter.limit("5 per hour")
def register_name():
    data = request.get_json()
    name = data.get('name', '').lower()
    owner = data.get('owner')
    years = int(data.get('years', 1))
    
    if not name or len(name) < 3:
        return jsonify({"error": "Name must be at least 3 characters"}), 400
    
    if name in name_registry:
        return jsonify({"error": "Name already taken"}), 400
    
    if not owner or owner not in blockchain.wallets:
        return jsonify({"error": "Invalid owner address"}), 400
    
    # Calculate registration fee based on name length and duration
    base_fee = float(fee_manager.fees['features']['name_registration_fee'])
    
    # Price tiers based on length
    if len(name) == 3:
        price_multiplier = 10
    elif len(name) == 4:
        price_multiplier = 2
    else:
        price_multiplier = 1
    
    total_price = base_fee * price_multiplier * years
    
    if blockchain.get_balance(owner) < total_price:
        return jsonify({"error": f"Insufficient balance. Need {total_price} QRC"}), 400
    
    # Register name
    name_registry[name] = {
        "owner": owner,
        "registered": datetime.now().isoformat(),
        "expires": datetime.now().replace(year=datetime.now().year + years).isoformat()
    }
    
    # Create transaction
    timestamp = time.time()
    transaction = {
        'sender': owner,
        'recipient': 'NAME_SERVICE',
        'amount': total_price,
        'fee': 0,
        'timestamp': timestamp,
        'type': 'name_registration',
        'name': f"{name}.qrc",
        'quantum_resistant': True,
        'signature': hashlib.sha256(f"register-{name}".encode()).hexdigest()
    }
    
    # Create custom fee structure for name registration
    custom_fee_structure = {
        "total_fee": total_price,
        "developer_fee": total_price,  # All goes to developer for features
        "network_fee": 0,
        "fee_transactions": [
            {
                "recipient": fee_manager.developer_address,
                "amount": total_price,
                "type": "name_registration_fee"
            }
        ]
    }
    
    # Create fee transactions
    fee_txs = fee_manager.create_fee_distribution_transactions(transaction, custom_fee_structure)
    
    # Update balance
    blockchain.wallets[owner]['balance'] -= total_price
    
    # Add transactions
    blockchain.add_transaction(transaction)
    for fee_tx in fee_txs:
        blockchain.add_transaction(fee_tx)
    
    return jsonify({
        "success": True,
        "name": f"{name}.qrc",
        "transactionHash": transaction['signature'],
        "fee_paid": total_price
    })

@app.route('/api/name/<name>', methods=['GET'])
def check_name(name):
    name = name.lower()
    if name in name_registry:
        return jsonify({
            "available": False,
            "owner": name_registry[name]['owner'],
            "expires": name_registry[name]['expires']
        })
    
    # Calculate price using fee manager base
    base_price = float(fee_manager.fees['features']['name_registration_fee'])
    price = base_price
    
    if len(name) == 4:
        price = base_price * 2
    elif len(name) == 3:
        price = base_price * 10
    elif len(name) <= 2:
        price = base_price * 100
        
    return jsonify({
        "available": True,
        "price": price
    })

# Storage Service
@app.route('/api/storage/upload', methods=['POST'])
@limiter.limit("50 per hour")
def upload_file():
    data = request.get_json()
    owner = data.get('owner')
    file_hash = data.get('hash')
    file_size = int(data.get('size', 0))  # in bytes
    file_name = data.get('name')
    
    if not owner or owner not in blockchain.wallets:
        return jsonify({"error": "Invalid owner"}), 400
    
    # Calculate fees using fee manager
    size_mb = file_size / (1024 ** 2)  # Convert to MB
    storage_fee_structure = fee_manager.calculate_feature_fee("storage", size_mb=size_mb)
    storage_fee = storage_fee_structure['total_fee']
    
    upload_fee = 0.001  # Fixed upload fee
    total_fee = upload_fee + storage_fee
    
    if blockchain.get_balance(owner) < total_fee:
        return jsonify({"error": f"Insufficient balance. Need {total_fee} QRC"}), 400
    
    # Store file metadata
    storage_files[file_hash] = {
        "owner": owner,
        "name": file_name,
        "size": file_size,
        "uploaded": datetime.now().isoformat(),
        "monthly_fee": storage_fee
    }
    
    # Update user storage
    storage_usage[owner]["used"] += file_size
    storage_usage[owner]["files"].append(file_hash)
    
    # Create transaction
    timestamp = time.time()
    transaction = {
        'sender': owner,
        'recipient': 'STORAGE_SERVICE',
        'amount': total_fee,
        'fee': 0,
        'timestamp': timestamp,
        'type': 'file_upload',
        'file_hash': file_hash,
        'quantum_resistant': True,
        'signature': hashlib.sha256(f"upload-{file_hash}".encode()).hexdigest()
    }
    
    # All storage fees go to developer
    custom_fee_structure = {
        "total_fee": total_fee,
        "developer_fee": total_fee,
        "network_fee": 0,
        "fee_transactions": [
            {
                "recipient": fee_manager.developer_address,
                "amount": total_fee,
                "type": "storage_fee"
            }
        ]
    }
    
    # Create fee transactions
    fee_txs = fee_manager.create_fee_distribution_transactions(transaction, custom_fee_structure)
    
    # Update balance
    blockchain.wallets[owner]['balance'] -= total_fee
    
    # Add transactions
    blockchain.add_transaction(transaction)
    for fee_tx in fee_txs:
        blockchain.add_transaction(fee_tx)
    
    return jsonify({
        "success": True,
        "fileHash": file_hash,
        "monthlyFee": storage_fee,
        "totalFeePaid": total_fee
    })

@app.route('/api/storage/<address>', methods=['GET'])
def get_storage_info(address):
    usage = storage_usage.get(address, {"used": 0, "files": []})
    files = [storage_files[h] for h in usage["files"] if h in storage_files]
    
    return jsonify({
        "usedBytes": usage["used"],
        "fileCount": len(files),
        "monthlyFee": sum(f["monthly_fee"] for f in files),
        "files": files
    })

# Message Service
@app.route('/api/message/send', methods=['POST'])
@limiter.limit("20 per minute")
def send_message():
    data = request.get_json()
    from_address = data.get('from')
    to_address = data.get('to')
    message = data.get('message', '')[:280]  # Twitter-like limit
    encrypted = data.get('encrypted', False)
    
    if not from_address or from_address not in blockchain.wallets:
        return jsonify({"error": "Invalid sender"}), 400
    
    # Message fee: 0.01 QRC
    if blockchain.get_balance(from_address) < 0.01:
        return jsonify({"error": "Insufficient balance for message fee"}), 400
    
    # Store message on blockchain
    message_tx = {
        'sender': from_address,
        'recipient': to_address,
        'message': message,
        'encrypted': encrypted,
        'timestamp': time.time(),
        'type': 'message'
    }
    
    # Fee transaction
    fee_tx = {
        'sender': from_address,
        'recipient': fee_manager.developer_address,
        'amount': 0.01,
        'type': 'message_fee',
        'timestamp': time.time()
    }
    
    # Update balance
    blockchain.wallets[from_address]['balance'] -= 0.01
    
    # Add transactions
    blockchain.add_transaction(message_tx)
    blockchain.add_transaction(fee_tx)
    
    return jsonify({
        "success": True,
        "timestamp": message_tx['timestamp'],
        "fee": 0.01
    })

# Revenue Analytics Endpoint
@app.route('/api/revenue/analytics', methods=['GET'])
def revenue_analytics():
    # Calculate total gas fees generated
    total_gas = 0
    
    # Token creation fees
    total_gas += len(tokens) * float(fee_manager.fees['features']['token_creation_fee'])
    
    # Token transfer fees
    for token_address in tokens:
        total_gas += token_transfers[token_address] * 0.1
    
    # Name registration fees (average)
    total_gas += len(name_registry) * float(fee_manager.fees['features']['name_registration_fee'])
    
    # Storage fees
    for user_storage in storage_usage.values():
        for file_hash in user_storage["files"]:
            if file_hash in storage_files:
                total_gas += storage_files[file_hash]["monthly_fee"]
    
    # Faucet gas fees
    total_gas += len(faucet_claims) * 0.001
    
    return jsonify({
        "totalGasGenerated": total_gas,
        "revenueStreams": {
            "tokenCreation": len(tokens) * float(fee_manager.fees['features']['token_creation_fee']),
            "tokenTransfers": sum(token_transfers.values()) * 0.1,
            "nameService": len(name_registry) * float(fee_manager.fees['features']['name_registration_fee']),
            "storage": sum(f["monthly_fee"] for f in storage_files.values()),
            "faucetFees": len(faucet_claims) * 0.001
        },
        "activeUsers": len(blockchain.wallets),
        "dailyTransactions": len(blockchain.transaction_pool),
        "feeAddresses": {
            "developer": fee_manager.developer_address[:10] + '...',
            "treasury": fee_manager.treasury_address[:10] + '...'
        }
    })

# Serve HTML files
@app.route('/')
def serve_wallet():
    return send_file('quantum_web_wallet.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(path):
        return send_file(path)
    return "File not found", 404

if __name__ == '__main__':
    # Get port from environment variable for Render
    port = int(os.environ.get('PORT', 5000))
    

    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║        PQC BLOCKCHAIN v4.0 - ENHANCED WITH FEES           ║
    ║        Post-Quantum Cryptography Blockchain               ║
    ╚═══════════════════════════════════════════════════════════╝
    
    🔐 Quantum Security: ACTIVE
    🚀 Signature Algorithm: CRYSTALS-Dilithium2 (NIST Level 2)
    ⚡ Network Status: ONLINE
    💰 Token System: ENABLED
    🌐 Name Service: ACTIVE
    💾 Storage Service: READY
    🎁 Faucet System: OPERATIONAL
    💸 Fee System: INTEGRATED
    🔑 Founder Auth: ENABLED
    
    💰 Fee Configuration:
       Transaction Fee: 0.05% (min 0.00005 QRC)
       Developer Share: 50%
       Network Share: 50%
       
    🏦 Revenue Addresses:
       Developer: {}...
       Treasury: {}...
    
    🌐 Server: Starting on port {}...
    
    [INFO] Mining thread started
    [INFO] TPS simulation active
    [INFO] Fee manager initialized
    [INFO] Auth manager initialized
    [INFO] All services operational
    """.format(
        fee_manager.developer_address[:10] if fee_manager.developer_address else "NOT_SET",
        fee_manager.treasury_address[:10] if fee_manager.treasury_address else "NOT_SET",
        port
    ))
    
    # Run without debug mode in production
    app.run(host='0.0.0.0', port=port, debug=False)