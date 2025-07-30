#!/usr/bin/env python3
"""
Elastic Cloud Connection Test Script
This script tests different authentication methods to diagnose connection issues.
"""

import os
import base64
import requests
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_basic_connection():
    """Test basic connection without authentication"""
    host = os.getenv("ELASTICSEARCH_HOST")
    logger.info(f"Testing basic connection to: {host}")
    
    try:
        response = requests.get(f"{host}/", timeout=10)
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.text[:200]}")
        return response.status_code
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return None

def test_api_key_auth():
    """Test API key authentication"""
    host = os.getenv("ELASTICSEARCH_HOST")
    username = os.getenv("ELASTICSEARCH_USERNAME")
    
    if not username:
        logger.error("No API key provided")
        return False
    
    try:
        # Decode the API key
        api_key = base64.b64decode(username).decode('utf-8')
        logger.info(f"Decoded API key: {api_key[:20]}...{api_key[-20:]}")
        
        # Test with requests first
        headers = {"Authorization": f"ApiKey {api_key}"}
        response = requests.get(f"{host}/", headers=headers, timeout=10)
        logger.info(f"API Key auth response: {response.status_code}")
        logger.info(f"Response body: {response.text[:200]}")
        
        # Test with Elasticsearch client
        client = Elasticsearch([host], api_key=api_key, verify_certs=True)
        info = client.info()
        logger.info(f"Elasticsearch client connection successful: {info['cluster_name']}")
        return True
        
    except Exception as e:
        logger.error(f"API key authentication failed: {e}")
        return False

def test_basic_auth():
    """Test basic username/password authentication"""
    host = os.getenv("ELASTICSEARCH_HOST")
    username = os.getenv("ELASTICSEARCH_USERNAME")
    password = os.getenv("ELASTICSEARCH_PASSWORD")
    
    if not username or not password:
        logger.error("Username or password not provided")
        return False
    
    try:
        # Test with requests first
        response = requests.get(f"{host}/", auth=(username, password), timeout=10)
        logger.info(f"Basic auth response: {response.status_code}")
        logger.info(f"Response body: {response.text[:200]}")
        
        # Test with Elasticsearch client
        client = Elasticsearch([host], basic_auth=(username, password), verify_certs=True)
        info = client.info()
        logger.info(f"Elasticsearch client connection successful: {info['cluster_name']}")
        return True
        
    except Exception as e:
        logger.error(f"Basic authentication failed: {e}")
        return False

def test_cloud_id():
    """Test cloud_id authentication if available"""
    cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
    username = os.getenv("ELASTICSEARCH_USERNAME")
    password = os.getenv("ELASTICSEARCH_PASSWORD")
    
    if not cloud_id:
        logger.info("No cloud_id provided")
        return False
    
    try:
        if username and not password:
            # Try API key with cloud_id
            api_key = base64.b64decode(username).decode('utf-8')
            client = Elasticsearch(cloud_id=cloud_id, api_key=api_key)
        else:
            # Try basic auth with cloud_id
            client = Elasticsearch(cloud_id=cloud_id, basic_auth=(username, password))
        
        info = client.info()
        logger.info(f"Cloud ID connection successful: {info['cluster_name']}")
        return True
        
    except Exception as e:
        logger.error(f"Cloud ID authentication failed: {e}")
        return False

def main():
    """Run all connection tests"""
    logger.info("🔍 Elastic Cloud Connection Diagnostics")
    logger.info("=" * 50)
    
    # Test basic connection
    logger.info("\n1. Testing basic connection...")
    basic_status = test_basic_connection()
    
    # Test API key authentication
    logger.info("\n2. Testing API key authentication...")
    api_key_success = test_api_key_auth()
    
    # Test basic authentication
    logger.info("\n3. Testing basic authentication...")
    basic_auth_success = test_basic_auth()
    
    # Test cloud_id
    logger.info("\n4. Testing cloud_id authentication...")
    cloud_id_success = test_cloud_id()
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 Connection Test Summary:")
    logger.info(f"Basic connection: {'✅' if basic_status == 401 else '❌'}")
    logger.info(f"API key auth: {'✅' if api_key_success else '❌'}")
    logger.info(f"Basic auth: {'✅' if basic_auth_success else '❌'}")
    logger.info(f"Cloud ID: {'✅' if cloud_id_success else '❌'}")
    
    if api_key_success or basic_auth_success or cloud_id_success:
        logger.info("\n🎉 At least one authentication method worked!")
    else:
        logger.info("\n❌ All authentication methods failed.")
        logger.info("Please check your Elastic Cloud API key permissions and format.")

if __name__ == "__main__":
    main() 