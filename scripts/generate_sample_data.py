#!/usr/bin/env python3
"""
Sample data generator for PayPal Merchant Troubleshooting App
This script creates sample merchant data in Elasticsearch for demonstration purposes.
"""

import json
import random
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Elasticsearch configuration
import os
from dotenv import load_dotenv

load_dotenv()

ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "localhost")
ELASTICSEARCH_PORT = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
ELASTICSEARCH_USERNAME = os.getenv("ELASTICSEARCH_USERNAME", "")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD", "")
INDEX_NAME = os.getenv("ELASTICSEARCH_INDEX", "paypal-merchants")

# Sample data
MERCHANT_NAMES = [
    "TechCorp Solutions", "Global Retail Inc", "Digital Marketplace", "E-Commerce Pro",
    "Online Store Plus", "WebShop Express", "Digital Goods Co", "Tech Retail Hub",
    "E-Business Solutions", "Digital Commerce Pro", "Web Store Central", "Online Market Hub",
    "Tech Solutions Inc", "Digital Retail Pro", "E-Commerce Central", "Web Business Hub",
    "Digital Store Pro", "Online Solutions Inc", "Tech Market Hub", "E-Retail Central"
]

COUNTRIES = ["US", "CA", "UK", "DE", "FR", "AU", "JP", "BR", "IN", "MX"]
CITIES = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]

def create_elasticsearch_client():
    """Create Elasticsearch client"""
    
    # Handle API key authentication for Elastic Cloud
    if ELASTICSEARCH_USERNAME and not ELASTICSEARCH_PASSWORD:
        # Use API key directly (no base64 decode for serverless)
        host_clean = ELASTICSEARCH_HOST.replace("https://", "").replace("http://", "")
        hosts = [{"host": host_clean, "port": int(ELASTICSEARCH_PORT), "scheme": "https"}]
        return Elasticsearch(
            hosts,
            api_key=ELASTICSEARCH_USERNAME,
            verify_certs=True
        )
    else:
        # Use traditional host/port connection
        return Elasticsearch([{
            'host': ELASTICSEARCH_HOST.replace('https://', '').replace('http://', ''),
            'port': ELASTICSEARCH_PORT
        }], 
        basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD) if ELASTICSEARCH_USERNAME else None,
        verify_certs=True if ELASTICSEARCH_HOST.startswith('https') else False)

def create_index(client):
    """Create the index with proper mapping"""
    try:
        # Check if index exists
        if client.indices.exists(index=INDEX_NAME):
            logger.info(f"Index {INDEX_NAME} already exists")
            return
        
        # Create index with mapping
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
            }
        }
        
        client.indices.create(index=INDEX_NAME, body=mapping)
        logger.info(f"Created index {INDEX_NAME}")
    except Exception as e:
        logger.error(f"Failed to create index: {e}")

def generate_merchant_data(merchant_id, merchant_name, base_date):
    """Generate sample data for a merchant"""
    # Base performance metrics
    base_conversion_rate = random.uniform(0.3, 0.8)
    base_error_rate = random.uniform(0.01, 0.15)
    base_transactions = random.randint(100, 5000)
    
    # Generate data for the last 3 months
    data_points = []
    for i in range(90):  # 90 days
        date = base_date - timedelta(days=i)
        
        # Add some variation to make it realistic
        conversion_variation = random.uniform(-0.1, 0.1)
        error_variation = random.uniform(-0.05, 0.05)
        transaction_variation = random.uniform(-0.2, 0.2)
        
        # Ensure values stay within reasonable bounds
        conversion_rate = max(0.01, min(1.0, base_conversion_rate + conversion_variation))
        error_rate = max(0.0, min(0.5, base_error_rate + error_variation))
        transaction_count = max(10, int(base_transactions * (1 + transaction_variation)))
        
        # Randomly add some issues
        if random.random() < 0.1:  # 10% chance of missing location
            country = None
            city = None
        else:
            country = random.choice(COUNTRIES)
            city = random.choice(CITIES)
        
        # Randomly add some conversion rate issues
        if random.random() < 0.05:  # 5% chance of low conversion rate
            conversion_rate = random.uniform(0.05, 0.25)
        
        # Randomly add some error rate issues
        if random.random() < 0.03:  # 3% chance of high error rate
            error_rate = random.uniform(0.15, 0.4)
        
        data_point = {
            "merchant_id": merchant_id,
            "merchant_name": merchant_name,
            "country": country,
            "city": city,
            "conversion_rate": round(conversion_rate, 4),
            "error_rate": round(error_rate, 4),
            "transaction_count": transaction_count,
            "timestamp": date.isoformat(),
            "status": random.choice(["active", "active", "active", "pending", "suspended"])
        }
        
        data_points.append(data_point)
    
    return data_points

def generate_sample_data():
    """Generate and insert sample data"""
    client = create_elasticsearch_client()
    
    # Create index
    create_index(client)
    
    # Generate data for each merchant
    base_date = datetime.now()
    all_data = []
    
    for i, merchant_name in enumerate(MERCHANT_NAMES):
        merchant_id = f"MERCH_{i+1:03d}"
        merchant_data = generate_merchant_data(merchant_id, merchant_name, base_date)
        all_data.extend(merchant_data)
        
        logger.info(f"Generated data for {merchant_name} ({merchant_id})")
    
    # Bulk insert data
    logger.info(f"Inserting {len(all_data)} data points...")
    
    bulk_data = []
    for doc in all_data:
        bulk_data.append({"index": {"_index": INDEX_NAME}})
        bulk_data.append(doc)
    
    try:
        response = client.bulk(body=bulk_data)
        if response.get('errors'):
            logger.error("Some errors occurred during bulk insert")
            for item in response['items']:
                if 'error' in item.get('index', {}):
                    logger.error(f"Error: {item['index']['error']}")
        else:
            logger.info("Successfully inserted all data")
    except Exception as e:
        logger.error(f"Failed to insert data: {e}")

def verify_data():
    """Verify that data was inserted correctly"""
    client = create_elasticsearch_client()
    
    try:
        # Get total count
        count_response = client.count(index=INDEX_NAME)
        total_docs = count_response['count']
        logger.info(f"Total documents in index: {total_docs}")
        
        # Get sample of documents
        sample_response = client.search(
            index=INDEX_NAME,
            body={"query": {"match_all": {}}, "size": 5}
        )
        
        logger.info("Sample documents:")
        for hit in sample_response['hits']['hits']:
            doc = hit['_source']
            logger.info(f"  {doc['merchant_name']} ({doc['merchant_id']}): "
                       f"Conversion: {doc['conversion_rate']:.2%}, "
                       f"Error: {doc['error_rate']:.2%}, "
                       f"Transactions: {doc['transaction_count']}")
        
        return total_docs > 0
    except Exception as e:
        logger.error(f"Failed to verify data: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting sample data generation...")
    
    # Generate data
    generate_sample_data()
    
    # Verify data
    if verify_data():
        logger.info("Sample data generation completed successfully!")
        logger.info(f"You can now run the application and access it at: http://localhost:8000")
    else:
        logger.error("Sample data generation failed!") 