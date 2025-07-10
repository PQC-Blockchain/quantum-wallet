import os

# Production settings
PORT = int(os.environ.get('PORT', 10000))
HOST = '0.0.0.0'
DEBUG = False

# Ensure environment variables are set
if not os.getenv('PQC_DEVELOPER_ADDRESS'):
    raise ValueError("PQC_DEVELOPER_ADDRESS not set in environment!")
    
if not os.getenv('PQC_TREASURY_ADDRESS'):
    raise ValueError("PQC_TREASURY_ADDRESS not set in environment!")