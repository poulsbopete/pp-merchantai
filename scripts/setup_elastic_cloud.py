#!/usr/bin/env python3
"""
Elastic Cloud Setup Script
This script helps set up the connection to Elastic Cloud and create the necessary index.
"""

import os
import base64
import json
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def decode_api_key(encoded_key):
    """Decode base64 encoded API key"""
    try:
        decoded = base64.b64decode(encoded_key).decode('utf-8')
        return decoded
    except Exception as e:
        logger.error(f"Failed to decode API key: {e}")
        return None

def create_elasticsearch_client():
    """Create Elasticsearch client for Elastic Cloud"""
    host = os.getenv("ELASTICSEARCH_HOST")
    port = os.getenv("ELASTICSEARCH_PORT", "443")
    username = os.getenv("ELASTICSEARCH_USERNAME")
    password = os.getenv("ELASTICSEARCH_PASSWORD")
    
    if not host:
        logger.error("ELASTICSEARCH_HOST not set in .env file")
        return None
    
        # Handle authentication
    if username and password:
        # Use username/password authentication
        logger.info("Using username/password authentication")
        client = Elasticsearch(
            [host],
            basic_auth=(username, password),
            verify_certs=True
        )
    elif username and not password:
        # Use API key directly (no base64 decode for serverless)
        logger.info("Using direct API key authentication")
        host_clean = host.replace("https://", "").replace("http://", "")
        hosts = [{"host": host_clean, "port": int(port), "scheme": "https"}]
        client = Elasticsearch(
            hosts,
            api_key=username,
            verify_certs=True
        )
    else:
        # No authentication
        logger.info("Using no authentication")
        client = Elasticsearch(
            [host],
            verify_certs=True
        )
    
    return client

def create_index_mapping(client, index_name):
    """Create index with proper mapping"""
    mapping = {
        "mappings": {
            "properties": {
                "merchant_id": {"type": "keyword"},
                "merchant_name": {"type": "text"},
                "country": {"type": "keyword"},
                "city": {"type": "keyword"},
                "conversion_rate": {"type": "float"},
                "error_rate": {"type": "float"},
                "transaction_count": {"type": "integer"},
                "timestamp": {"type": "date"},
                "status": {"type": "keyword"}
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }
    }
    
    try:
        # Check if index exists
        if client.indices.exists(index=index_name):
            logger.info(f"Index '{index_name}' already exists")
            return True
        
        # Create index
        response = client.indices.create(index=index_name, body=mapping)
        logger.info(f"Index '{index_name}' created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create index: {e}")
        return False

def test_connection(client):
    """Test Elasticsearch connection"""
    try:
        info = client.info()
        logger.info(f"Connected to Elasticsearch cluster: {info['cluster_name']}")
        logger.info(f"Elasticsearch version: {info['version']['number']}")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {e}")
        return False

def main():
    """Main setup function"""
    logger.info("🔧 Setting up Elastic Cloud connection...")
    
    # Create client
    client = create_elasticsearch_client()
    if not client:
        logger.error("Failed to create Elasticsearch client")
        return
    
    # Test connection
    if not test_connection(client):
        logger.error("Failed to connect to Elasticsearch")
        return
    
    # Get index name from environment
    index_name = os.getenv("ELASTICSEARCH_INDEX", "paypal-merchants")
    
    # Create index
    if create_index_mapping(client, index_name):
        logger.info("✅ Elastic Cloud setup completed successfully!")
        logger.info(f"Index '{index_name}' is ready for data")
    else:
        logger.error("❌ Failed to create index")

if __name__ == "__main__":
    main() 