# payment_api_addon.py - Add these routes to your quantum_blockchain_server_v3.py

# Add these imports at the top
import uuid
import hashlib

# Payment tracking
payments = {}  # In production, use a database

@app.route('/api/payment/create', methods=['POST'])
def create_payment_request():
    """Create a payment request for merchants"""
    try:
        data = request.json
        
        # Validate required fields
        amount = float(data.get('amount', 0))
        merchant_wallet = data.get('merchant_wallet')
        description = data.get('description', '')
        callback_url = data.get('callback_url', '')
        
        if not merchant_wallet or amount <= 0:
            return jsonify({'success': False, 'error': 'Invalid payment details'})
        
        # Generate unique payment ID
        payment_id = str(uuid.uuid4())
        
        # Create payment request
        payment = {
            'id': payment_id,
            'merchant_wallet': merchant_wallet,
            'amount': amount,
            'description': description,
            'callback_url': callback_url,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'tx_hash': None
        }
        
        payments[payment_id] = payment
        
        # Generate payment URL
        payment_url = f"https://pqc-blockchain.onrender.com/pay/{payment_id}"
        
        return jsonify({
            'success': True,
            'payment_id': payment_id,
            'payment_url': payment_url,
            'amount': amount,
            'merchant_wallet': merchant_wallet
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/payment/status/<payment_id>')
def check_payment_status(payment_id):
    """Check payment status"""
    payment = payments.get(payment_id)
    
    if not payment:
        return jsonify({'success': False, 'error': 'Payment not found'})
    
    return jsonify({
        'success': True,
        'payment': payment
    })

@app.route('/pay/<payment_id>')
def payment_page(payment_id):
    """Payment page for customers"""
    return send_file('payment_page.html')

@app.route('/api/payment/complete', methods=['POST'])
def complete_payment():
    """Mark payment as complete when transaction is confirmed"""
    try:
        data = request.json
        payment_id = data.get('payment_id')
        tx_hash = data.get('tx_hash')
        
        payment = payments.get(payment_id)
        if not payment:
            return jsonify({'success': False, 'error': 'Payment not found'})
        
        # Update payment status
        payment['status'] = 'completed'
        payment['tx_hash'] = tx_hash
        payment['completed_at'] = datetime.now().isoformat()
        
        # In production, trigger webhook to merchant
        if payment['callback_url']:
            # Send webhook notification
            pass
        
        return jsonify({'success': True, 'payment': payment})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# API Documentation endpoint
@app.route('/api/docs')
def api_documentation():
    """Return API documentation"""
    docs = {
        'endpoints': {
            'create_payment': {
                'url': '/api/payment/create',
                'method': 'POST',
                'params': {
                    'amount': 'float - Amount in QRC',
                    'merchant_wallet': 'string - Your QRC wallet address',
                    'description': 'string - Payment description',
                    'callback_url': 'string - Webhook URL for notifications'
                },
                'response': {
                    'payment_id': 'string - Unique payment ID',
                    'payment_url': 'string - URL for customer to pay'
                }
            },
            'check_status': {
                'url': '/api/payment/status/{payment_id}',
                'method': 'GET',
                'response': {
                    'status': 'pending | completed | failed',
                    'tx_hash': 'string - Transaction hash when completed'
                }
            }
        },
        'example_integration': {
            'php': '''
// Create payment
$payment = curl_post('https://pqc-blockchain.onrender.com/api/payment/create', [
    'amount' => 99.99,
    'merchant_wallet' => 'Q123456789',
    'description' => 'Order #12345'
]);

// Redirect customer
header('Location: ' . $payment['payment_url']);
            ''',
            'javascript': '''
// Create payment
const response = await fetch('https://pqc-blockchain.onrender.com/api/payment/create', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        amount: 99.99,
        merchant_wallet: 'Q123456789',
        description: 'Order #12345'
    })
});

const payment = await response.json();
window.location.href = payment.payment_url;
            '''
        }
    }
    
    return jsonify(docs)