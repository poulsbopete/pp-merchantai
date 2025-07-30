#!/usr/bin/env python3
"""
Direct API Key Test
Tests different API key formats to match working apps.
"""

import os
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

def test_api_key_direct():
    """Test with API key directly (no base64 decode)"""
    print("Testing with API key directly...")
    
    host = os.getenv("ELASTICSEARCH_HOST")
    api_key = os.getenv("ELASTICSEARCH_USERNAME")
    
    try:
        client = Elasticsearch(
            [host],
            api_key=api_key,
            verify_certs=True
        )
        
        info = client.info()
        print(f"✅ Direct API key works: {info['cluster_name']}")
        return True
    except Exception as e:
        print(f"❌ Direct API key failed: {e}")
        return False

def test_api_key_decoded():
    """Test with decoded API key"""
    print("Testing with decoded API key...")
    
    import base64
    host = os.getenv("ELASTICSEARCH_HOST")
    encoded_key = os.getenv("ELASTICSEARCH_USERNAME")
    
    try:
        api_key = base64.b64decode(encoded_key).decode('utf-8')
        client = Elasticsearch(
            [host],
            api_key=api_key,
            verify_certs=True
        )
        
        info = client.info()
        print(f"✅ Decoded API key works: {info['cluster_name']}")
        return True
    except Exception as e:
        print(f"❌ Decoded API key failed: {e}")
        return False

def test_basic_auth():
    """Test with basic auth (username:password format)"""
    print("Testing with basic auth...")
    
    import base64
    host = os.getenv("ELASTICSEARCH_HOST")
    encoded_key = os.getenv("ELASTICSEARCH_USERNAME")
    
    try:
        decoded = base64.b64decode(encoded_key).decode('utf-8')
        username, password = decoded.split(':', 1)
        
        client = Elasticsearch(
            [host],
            basic_auth=(username, password),
            verify_certs=True
        )
        
        info = client.info()
        print(f"✅ Basic auth works: {info['cluster_name']}")
        return True
    except Exception as e:
        print(f"❌ Basic auth failed: {e}")
        return False

def main():
    print("🔍 Testing Different API Key Formats")
    print("=" * 50)
    
    host = os.getenv("ELASTICSEARCH_HOST")
    api_key = os.getenv("ELASTICSEARCH_USERNAME")
    
    print(f"Host: {host}")
    print(f"API Key: {api_key[:20]}...{api_key[-20:]}")
    print()
    
    # Test different formats
    success = False
    
    if test_api_key_direct():
        success = True
    elif test_api_key_decoded():
        success = True
    elif test_basic_auth():
        success = True
    
    if success:
        print("\n🎉 Found working connection method!")
        print("Your PayPal Merchant AI app should work now.")
    else:
        print("\n❌ All connection methods failed.")
        print("Please check your API key format and permissions.")

if __name__ == "__main__":
    main() 