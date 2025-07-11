# setup_founder_wallet.py
# Run this script to set up your founder wallet with 2FA

import requests
import json
import base64
import os
from getpass import getpass

# Configuration
SERVER_URL = "http://localhost:5000"  # Change to your server URL if different
FOUNDER_ADDRESS = "QRC7K9mN3pX2vB8nQ4jL6wR5tY1aZ9fH3kE-A7F2"  # Your founder wallet address
ADMIN_KEY = "#C?^3Zux$lY@w,};YT*/ey>gU?C6HK"  # This should match what's in your server

def setup_founder_wallet():
    print("=== QRC Founder Wallet Setup ===\n")
    
    # Get password
    print("Create a strong password for your founder wallet")
    print("(This password will be required every time you login)\n")
    
    while True:
        password = getpass("Enter password (minimum 12 characters): ")
        
        if len(password) < 12:
            print("❌ Password must be at least 12 characters. Try again.\n")
            continue
            
        confirm = getpass("Confirm password: ")
        
        if password != confirm:
            print("❌ Passwords don't match. Try again.\n")
            continue
            
        break
    
    print("\n🔄 Registering founder wallet...")
    
    # Register the wallet
    try:
        response = requests.post(f"{SERVER_URL}/api/auth/register-founder", json={
            "admin_key": ADMIN_KEY,
            "address": FOUNDER_ADDRESS,
            "password": password
        })
        
        if response.status_code == 403:
            print("❌ Invalid admin key. Check your server configuration.")
            return
            
        data = response.json()
        
        if not data.get('success'):
            print(f"❌ Registration failed: {data.get('error', 'Unknown error')}")
            return
            
        print("✅ Founder wallet registered successfully!")
        print("\n" + "="*50)
        print("IMPORTANT - SAVE THIS INFORMATION:")
        print("="*50)
        print(f"\n📱 2FA Secret Key: {data['secret']}")
        print("\n⚠️  SETUP INSTRUCTIONS:")
        print("1. Install Google Authenticator on your phone")
        print("2. Open the app and tap '+' to add new account")
        print("3. Select 'Enter a setup key'")
        print("4. Enter these details:")
        print(f"   - Account name: QRC Founder")
        print(f"   - Key: {data['secret']}")
        print("   - Type: Time based")
        print("5. Tap 'Add'\n")
        
        # Save QR code
        if 'qr_code' in data:
            qr_data = data['qr_code'].split(',')[1]
            qr_bytes = base64.b64decode(qr_data)
            
            filename = f"founder_2fa_qr.png"
            with open(filename, 'wb') as f:
                f.write(qr_bytes)
            
            print(f"📸 QR code saved as: {filename}")
            print("   (You can scan this instead of manual entry)")
        
        print("\n" + "="*50)
        print("WRITE DOWN YOUR 2FA SECRET KEY!")
        print("You'll need it if you lose your phone")
        print("="*50)
        
        # Test login
        input("\nPress Enter when you've set up Google Authenticator...")
        test = input("Would you like to test login now? (y/n): ")
        if test.lower() == 'y':
            test_login(FOUNDER_ADDRESS, password)
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server.")
        print("   Make sure your blockchain server is running!")
        print("   Run: python pqc_blockchain_server_enhanced.py")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_login(address, password):
    print("\n=== Testing Login ===")
    
    # Step 1: Verify password
    print("🔐 Verifying password...")
    response = requests.post(f"{SERVER_URL}/api/auth/verify-password", json={
        "address": address,
        "password": password
    })
    
    data = response.json()
    if not data.get('success'):
        print(f"❌ Password verification failed: {data.get('error')}")
        return
        
    print("✅ Password verified")
    temp_token = data.get('temp_token')
    
    # Step 2: Get 2FA code
    otp = input("📱 Enter 6-digit code from Google Authenticator: ")
    
    # Step 3: Verify 2FA
    print("🔑 Verifying 2FA...")
    response = requests.post(f"{SERVER_URL}/api/auth/verify-2fa", json={
        "temp_token": temp_token,
        "otp": otp,
        "device_id": "setup-script",
        "remember_device": False
    })
    
    data = response.json()
    if data.get('success'):
        print("\n✅ Login successful!")
        print(f"🎉 Wallet balance: {data['wallet_data']['balance']} QRC")
        print("👑 Founder status confirmed")
        print("\n🌐 You can now login through the web wallet!")
    else:
        print(f"❌ 2FA verification failed: {data.get('error')}")
        print("   Make sure the code is correct and your device time is synced")

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║             QRC BLOCKCHAIN FOUNDER WALLET SETUP            ║
    ╚═══════════════════════════════════════════════════════════╝
    
    This script will:
    1. Register your founder wallet
    2. Set up 2FA authentication
    3. Test the login process
    
    Make sure:
    - Your blockchain server is running
    - You have Google Authenticator installed on your phone
    """)
    
    input("Press Enter to continue...")
    setup_founder_wallet()