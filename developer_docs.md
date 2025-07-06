# QRC Blockchain Developer Documentation

## Overview

QRC is a quantum-resistant blockchain with 1,773 TPS proven performance. This guide helps developers integrate QRC payments and build on our platform.

## Quick Start

### 1. Create a Merchant Wallet

Visit https://pqc-blockchain.onrender.com and create a wallet. Save your wallet address (starts with Q).

### 2. Accept QRC Payments

#### Simple Payment Button

Add this to your website:

```html
<script src="https://pqc-blockchain.onrender.com/pay.js"></script>
<button onclick="payWithQRC(99.99, 'Q_YOUR_WALLET_ADDRESS', 'Product Purchase')">
  Pay 99.99 QRC
</button>
```

#### Advanced Integration

```javascript
// Create payment request
const payment = await fetch('https://pqc-blockchain.onrender.com/api/payment/create', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    amount: 99.99,
    merchant_wallet: 'Q_YOUR_WALLET_ADDRESS',
    description: 'Order #12345',
    callback_url: 'https://yoursite.com/webhook'
  })
});

const data = await payment.json();
// Redirect customer to payment page
window.location.href = data.payment_url;
```

## API Reference

### Base URL
```
https://pqc-blockchain.onrender.com/api
```

### Endpoints

#### Create Payment
```http
POST /payment/create
Content-Type: application/json

{
  "amount": 99.99,
  "merchant_wallet": "Q123456789",
  "description": "Order #12345",
  "callback_url": "https://yoursite.com/webhook"
}
```

Response:
```json
{
  "success": true,
  "payment_id": "uuid",
  "payment_url": "https://pqc-blockchain.onrender.com/pay/uuid",
  "amount": 99.99
}
```

#### Check Payment Status
```http
GET /payment/status/{payment_id}
```

Response:
```json
{
  "success": true,
  "payment": {
    "status": "completed",
    "tx_hash": "QTX123456789",
    "amount": 99.99,
    "completed_at": "2025-01-10T10:00:00Z"
  }
}
```

#### Get Wallet Balance
```http
GET /wallet/balance/{address}
```

#### Get Blockchain Stats
```http
GET /stats
```

## Integration Examples

### PHP/WordPress

```php
<?php
// QRC Payment Plugin
function create_qrc_payment($amount, $order_id) {
    $api_url = 'https://pqc-blockchain.onrender.com/api/payment/create';
    
    $data = array(
        'amount' => $amount,
        'merchant_wallet' => get_option('qrc_wallet_address'),
        'description' => 'Order #' . $order_id,
        'callback_url' => site_url('/qrc-webhook')
    );
    
    $response = wp_remote_post($api_url, array(
        'headers' => array('Content-Type' => 'application/json'),
        'body' => json_encode($data)
    ));
    
    $body = json_decode(wp_remote_retrieve_body($response), true);
    
    if ($body['success']) {
        return $body['payment_url'];
    }
    
    return false;
}

// Handle webhook
function handle_qrc_webhook() {
    $payment_id = $_POST['payment_id'];
    $status = $_POST['status'];
    
    if ($status === 'completed') {
        // Mark order as paid
        update_order_status($payment_id, 'paid');
    }
}
```

### Node.js/Express

```javascript
const express = require('express');
const axios = require('axios');

// Create payment
app.post('/checkout', async (req, res) => {
    try {
        const payment = await axios.post(
            'https://pqc-blockchain.onrender.com/api/payment/create',
            {
                amount: req.body.amount,
                merchant_wallet: process.env.QRC_WALLET,
                description: `Order ${req.body.orderId}`,
                callback_url: 'https://mysite.com/qrc/webhook'
            }
        );
        
        res.redirect(payment.data.payment_url);
    } catch (error) {
        res.status(500).send('Payment creation failed');
    }
});

// Webhook handler
app.post('/qrc/webhook', (req, res) => {
    const { payment_id, status, tx_hash } = req.body;
    
    if (status === 'completed') {
        // Update order in database
        db.orders.update(payment_id, { 
            paid: true, 
            tx_hash: tx_hash 
        });
    }
    
    res.status(200).send('OK');
});
```

### Python/Django

```python
import requests
from django.shortcuts import redirect

def create_payment(request):
    # Create QRC payment
    response = requests.post(
        'https://pqc-blockchain.onrender.com/api/payment/create',
        json={
            'amount': 99.99,
            'merchant_wallet': settings.QRC_WALLET,
            'description': f'Order {order.id}',
            'callback_url': request.build_absolute_uri('/qrc-webhook/')
        }
    )
    
    data = response.json()
    if data['success']:
        return redirect(data['payment_url'])
    
    return HttpResponse('Payment failed', status=500)
```

## Best Practices

### 1. Security
- Never expose private keys
- Verify webhook signatures (coming soon)
- Use HTTPS for callbacks

### 2. User Experience
- Show QRC prices in USD equivalent
- Provide clear payment instructions
- Handle errors gracefully

### 3. Testing
- Use testnet tokens from faucet
- Test edge cases (insufficient balance, network delays)

## Building on QRC

### Smart Contracts (Coming Soon)
- EVM-compatible
- Quantum-resistant signatures
- Gas paid in QRC

### Token Creation
- Create your own tokens on QRC
- Automatic quantum protection
- Low fees

## Resources

- **GitHub**: https://github.com/PQC-Blockchain/pqc-blockchain
- **Explorer**: https://pqc-blockchain.onrender.com/explorer
- **Support**: developers@qrcblockchain.com (set this up)

## Developer Incentives

### Grant Program
- 100,000 QRC for useful integrations
- 500,000 QRC for major platforms (Shopify, WooCommerce)
- 1,000,000 QRC for enterprise solutions

### How to Apply
1. Build integration
2. Submit PR to our GitHub
3. Include demo and documentation
4. Receive grant upon approval

## Roadmap

- **Q1 2025**: Payment API (Live ✓)
- **Q2 2025**: Smart contracts
- **Q3 2025**: Cross-chain bridge
- **Q4 2025**: Mobile SDKs

## Get Started Today

1. Create wallet: https://pqc-blockchain.onrender.com
2. Get test QRC from faucet
3. Try the payment API
4. Join our developer community

Questions? Reach out on GitHub or Discord.