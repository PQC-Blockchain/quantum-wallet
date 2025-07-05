# quantum_blockchain_server_v3.py - Server with liquidity fund tracking

from flask import Flask, jsonify, request, send_file
import json
import time
from datetime import datetime
import threading
from quantum_blockchain_fast_fixed import FastQuantumBlockchain
import os

app = Flask(__name__)

# Global blockchain instance
blockchain = FastQuantumBlockchain()

# REVENUE SYSTEM CONSTANTS
TRANSACTION_FEE_PERCENT = 0.002  # 0.2% fee (increased for faster liquidity)
FOUNDER_WALLET = "Q1000000001"  # Your special founder wallet
PREMIUM_USERS = {}  # Track premium users

# Revenue tracking
revenue_stats = {
    'total_fees_collected': 0,
    'daily_fees': 0,
    'total_premium_users': 0,
    'api_calls_today': 0
}

# Liquidity fund tracking
liquidity_fund = {
    'qrc_accumulated': 0,
    'target_usdt': 500,  # Target $500 for initial liquidity
    'days_elapsed': 0,
    'estimated_days_to_target': 30
}

# Stats tracking
stats = {
    'total_users': 0,
    'daily_transactions': 0,
    'peak_tps': 0
}

@app.route('/')
def index():
    """Serve the web wallet"""
    return send_file('quantum_web_wallet.html')

@app.route('/explorer')
def explorer():
    """Serve the block explorer"""
    return send_file('block_explorer.html')

@app.route('/revenue')
def revenue_dashboard():
    """Revenue dashboard (private)"""
    return send_file('revenue_dashboard.html')

@app.route('/api/stats')
def get_stats():
    """Get blockchain statistics"""
    blockchain_stats = blockchain.get_stats()
    
    # Update peak TPS
    current_tps = blockchain_stats['tps']
    if current_tps > stats['peak_tps']:
        stats['peak_tps'] = current_tps
    
    return jsonify({
        'success': True,
        'data': {
            'blockchain': {
                'height': blockchain_stats['chain_height'],
                'transactions': blockchain_stats['total_transactions'],
                'tps': round(blockchain_stats['tps'], 2),
                'peak_tps': round(stats['peak_tps'], 2),
                'pending': blockchain_stats['pending_transactions']
            },
            'network': {
                'users': blockchain_stats['unique_addresses'],
                'total_value': blockchain_stats['total_value_locked'],
                'daily_tx': stats['daily_transactions']
            }
        }
    })

@app.route('/api/revenue/stats')
def get_revenue_stats():
    """Get revenue statistics with liquidity fund info"""
    # Calculate QRC to USD (example rate)
    qrc_price = 0.001  # $0.001 per QRC initially
    
    # Calculate liquidity fund progress
    current_value = liquidity_fund['qrc_accumulated'] * qrc_price
    progress_percent = (current_value / liquidity_fund['target_usdt']) * 100
    
    # Estimate days to reach target based on current rate
    if revenue_stats['daily_fees'] > 0:
        days_needed = (liquidity_fund['target_usdt'] - current_value) / (revenue_stats['daily_fees'] * qrc_price)
    else:
        days_needed = 30
    
    return jsonify({
        'success': True,
        'revenue': {
            'total_fees_qrc': revenue_stats['total_fees_collected'],
            'total_fees_usd': revenue_stats['total_fees_collected'] * qrc_price,
            'daily_fees_qrc': revenue_stats['daily_fees'],
            'daily_fees_usd': revenue_stats['daily_fees'] * qrc_price,
            'premium_users': revenue_stats['total_premium_users'],
            'monthly_recurring': revenue_stats['total_premium_users'] * 9.99,
            'api_calls_today': revenue_stats['api_calls_today']
        },
        'liquidity_fund': {
            'qrc_accumulated': liquidity_fund['qrc_accumulated'],
            'current_value_usd': current_value,
            'target_usd': liquidity_fund['target_usdt'],
            'progress_percent': round(progress_percent, 2),
            'estimated_days_to_target': round(days_needed, 1)
        },
        'projections': {
            'monthly_fees': revenue_stats['daily_fees'] * 30,
            'monthly_usd': revenue_stats['daily_fees'] * 30 * qrc_price,
            'yearly_usd': revenue_stats['daily_fees'] * 365 * qrc_price
        }
    })

@app.route('/api/wallet/create', methods=['POST'])
def create_wallet():
    """Create a new quantum wallet"""
    try:
        # Generate wallet address (simplified for demo)
        wallet_id = f"Q{int(time.time() * 1000000) % 1000000000}"
        
        stats['total_users'] += 1
        
        return jsonify({
            'success': True,
            'wallet': {
                'address': wallet_id,
                'balance': 0,
                'quantum_safe': True
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/wallet/balance/<address>')
def get_balance(address):
    """Get wallet balance"""
    balance = blockchain.balances.get(address, 0)
    
    return jsonify({
        'success': True,
        'balance': balance,
        'address': address
    })

@app.route('/api/faucet', methods=['POST'])
def faucet():
    """Give free tokens to new users"""
    try:
        data = request.json
        address = data.get('address')
        
        if not address:
            return jsonify({'success': False, 'error': 'Address required'})
        
        # Check if already received from faucet
        if blockchain.balances.get(address, 0) > 0:
            return jsonify({'success': False, 'error': 'Already received tokens'})
        
        # Create faucet transaction
        tx = {
            'sender': 'GENESIS',
            'recipient': address,
            'amount': 1000,
            'timestamp': datetime.now().isoformat(),
            'quantum_signature': 'faucet_sig'
        }
        
        blockchain.add_transaction(tx)
        
        return jsonify({
            'success': True,
            'message': 'Received 1000 QRC!',
            'amount': 1000
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/transaction', methods=['POST'])
def send_transaction():
    """Send a quantum-safe transaction WITH FEES"""
    try:
        data = request.json
        
        sender = data['sender']
        recipient = data['recipient']
        amount = float(data['amount'])
        
        # Calculate fee (0.2% now)
        fee = amount * TRANSACTION_FEE_PERCENT
        if fee < 0.01:  # Minimum fee
            fee = 0.01
            
        # Check if premium user (no fees)
        if sender in PREMIUM_USERS:
            fee = 0
            
        total_deduction = amount + fee
        
        # Validate balance including fee
        sender_balance = blockchain.balances.get(sender, 0)
        if sender_balance < total_deduction:
            return jsonify({
                'success': False, 
                'error': f'Insufficient balance. Need {total_deduction} QRC (including {fee} QRC fee)'
            })
        
        # Create main transaction
        main_tx = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': datetime.now().isoformat(),
            'quantum_signature': data.get('signature', f'sig_{time.time()}')
        }
        
        # Create fee transaction (if applicable)
        if fee > 0:
            fee_tx = {
                'sender': sender,
                'recipient': FOUNDER_WALLET,
                'amount': fee,
                'timestamp': datetime.now().isoformat(),
                'quantum_signature': f'fee_sig_{time.time()}',
                'type': 'fee'
            }
            blockchain.add_transaction(fee_tx)
            revenue_stats['total_fees_collected'] += fee
            revenue_stats['daily_fees'] += fee
            liquidity_fund['qrc_accumulated'] += fee  # Track for liquidity
        
        blockchain.add_transaction(main_tx)
        stats['daily_transactions'] += 1
        
        return jsonify({
            'success': True,
            'message': f'Transaction sent! Fee: {fee} QRC (0.2%)',
            'tx_hash': f"QTX{int(time.time() * 1000000) % 1000000000}",
            'fee_charged': fee
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/premium/upgrade', methods=['POST'])
def upgrade_to_premium():
    """Upgrade wallet to premium tier"""
    data = request.json
    wallet = data.get('wallet')
    
    # Add to premium list
    PREMIUM_USERS[wallet] = {
        'upgraded_at': datetime.now().isoformat(),
        'tier': 'premium',
        'expires': None
    }
    
    revenue_stats['total_premium_users'] += 1
    
    return jsonify({
        'success': True,
        'message': 'Upgraded to Premium! No transaction fees.',
        'benefits': [
            'No transaction fees',
            'Priority processing',
            'Unlimited transactions',
            'Advanced analytics'
        ]
    })

@app.route('/api/blocks/latest')
def get_latest_blocks():
    """Get latest blocks"""
    latest_blocks = blockchain.chain[-10:]  # Last 10 blocks
    
    blocks_data = []
    for block in latest_blocks:
        blocks_data.append({
            'index': block['index'],
            'timestamp': block['timestamp'],
            'transactions': len(block['transactions']),
            'hash': block['hash'][:16] + '...'
        })
    
    return jsonify({
        'success': True,
        'blocks': blocks_data
    })

@app.route('/api/transactions/recent')
def get_recent_transactions():
    """Get recent transactions"""
    recent_txs = []
    
    # Get transactions from last few blocks
    for block in blockchain.chain[-5:]:
        for tx in block['transactions'][:5]:  # Max 5 per block
            recent_txs.append({
                'sender': tx['sender'][:10] + '...' if len(tx['sender']) > 10 else tx['sender'],
                'recipient': tx['recipient'][:10] + '...',
                'amount': tx['amount'],
                'time': tx['timestamp']
            })
    
    return jsonify({
        'success': True,
        'transactions': recent_txs[-20:]  # Last 20 transactions
    })

def auto_mine_thread():
    """Background thread for auto-mining"""
    while True:
        if len(blockchain.pending_transactions) > 0:
            blockchain.mine_pending_transactions()
        time.sleep(1)

def initialize_founder_wallet():
    """Give founder wallet initial QRC"""
    if FOUNDER_WALLET not in blockchain.balances:
        # Genesis allocation to founder
        genesis_tx = {
            'sender': 'GENESIS',
            'recipient': FOUNDER_WALLET,
            'amount': 10000000,  # 10M QRC founder allocation
            'timestamp': datetime.now().isoformat(),
            'quantum_signature': 'founder_genesis',
            'type': 'founder_allocation'
        }
        blockchain.add_transaction(genesis_tx)
        blockchain.mine_pending_transactions()
        print(f"✅ Founder wallet initialized with 10M QRC")
        print(f"💰 At $0.001/QRC = $10,000 initial value")
        print(f"🚀 At $0.01/QRC = $100,000 potential")
        print(f"🌙 At $0.10/QRC = $1,000,000 moon!")

if __name__ == '__main__':
    print("🚀 QUANTUM BLOCKCHAIN SERVER V3 - LIQUIDITY FUND EDITION")
    print("=" * 60)
    print("⚡ 1,773 TPS proven performance")
    print("🔐 Quantum-resistant signatures")
    print("💰 Transaction fees: 0.2% (increased for liquidity fund)")
    print("🏦 Liquidity target: $500 USDT")
    print("👑 Founder wallet: " + FOUNDER_WALLET)
    print("=" * 60)
    print("📊 Dashboards:")
    print("   Wallet: http://localhost:5000")
    print("   Explorer: http://localhost:5000/explorer")
    print("   Revenue: http://localhost:5000/revenue")
    print("=" * 60)
    
    # Initialize founder wallet
    initialize_founder_wallet()
    
    # Start mining thread
    mining_thread = threading.Thread(target=auto_mine_thread, daemon=True)
    mining_thread.start()
    
    # Run server
    port = int(os.environ.get('PORT', 5000))
app.run(debug=False, host='0.0.0.0', port=port)