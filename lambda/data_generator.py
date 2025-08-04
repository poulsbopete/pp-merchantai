import json
import random
import logging
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
ELASTICSEARCH_HOST = os.environ.get("ELASTICSEARCH_HOST", "https://ai-assistants-ffcafb.es.us-east-1.aws.elastic.cloud")
ELASTICSEARCH_USERNAME = os.environ.get("ELASTICSEARCH_USERNAME", "VFpHZFpwZ0JuckxKTnZGLTF5SE46dFpMNGxfV3pEbVJYZTFRZHRNZkg4UQ==")
ELASTICSEARCH_INDEX = os.environ.get("ELASTICSEARCH_INDEX", "pp-merchantai")

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
    try:
        # Handle API key authentication for Elastic Cloud
        host_clean = ELASTICSEARCH_HOST.replace("https://", "").replace("http://", "")
        hosts = [{"host": host_clean, "port": 443, "scheme": "https"}]
        
        return Elasticsearch(
            hosts,
            api_key=ELASTICSEARCH_USERNAME,
            verify_certs=True
        )
    except Exception as e:
        logger.error(f"Failed to create Elasticsearch client: {e}")
        raise

def generate_hourly_data():
    """Generate hourly data for all merchants"""
    client = create_elasticsearch_client()
    current_time = datetime.now()
    
    # Generate data for each merchant
    all_data = []
    
    for i, merchant_name in enumerate(MERCHANT_NAMES):
        merchant_id = f"MERCH_{i+1:03d}"
        
        # Define problematic merchants for testing
        problematic_merchants = {
            0: {"type": "conversion_rate", "rate": 0.15},  # TechCorp Solutions - low conversion
            1: {"type": "error_rate", "rate": 0.25},       # Global Retail Inc - high error rate
            2: {"type": "both", "conversion": 0.12, "error": 0.18},  # Digital Marketplace - both issues
            3: {"type": "conversion_rate", "rate": 0.18},  # E-Commerce Pro - low conversion
            4: {"type": "error_rate", "rate": 0.22},       # Online Store Plus - high error rate
            5: {"type": "conversion_rate", "rate": 0.22},  # WebShop Express - low conversion
            6: {"type": "error_rate", "rate": 0.19},       # Digital Goods Co - high error rate
            7: {"type": "both", "conversion": 0.14, "error": 0.16},  # Tech Retail Hub - both issues
            8: {"type": "conversion_rate", "rate": 0.16},  # E-Business Solutions - low conversion
            9: {"type": "error_rate", "rate": 0.21},       # Digital Commerce Pro - high error rate
        }
        
        # Base performance metrics
        if i in problematic_merchants:
            issue = problematic_merchants[i]
            if issue["type"] == "conversion_rate":
                base_conversion_rate = issue["rate"]
                base_error_rate = random.uniform(0.01, 0.08)
            elif issue["type"] == "error_rate":
                base_conversion_rate = random.uniform(0.4, 0.7)
                base_error_rate = issue["rate"]
            elif issue["type"] == "both":
                base_conversion_rate = issue["conversion"]
                base_error_rate = issue["error"]
        else:
            # Normal merchants with good performance
            base_conversion_rate = random.uniform(0.3, 0.8)
            base_error_rate = random.uniform(0.01, 0.15)
        
        base_transactions = random.randint(100, 5000)
        
        # Add some variation to make it realistic
        conversion_variation = random.uniform(-0.1, 0.1)
        error_variation = random.uniform(-0.05, 0.05)
        transaction_variation = random.uniform(-0.2, 0.2)
        
        # Ensure values stay within reasonable bounds
        conversion_rate = max(0.01, min(1.0, base_conversion_rate + conversion_variation))
        error_rate = max(0.0, min(0.5, base_error_rate + error_variation))
        transaction_count = max(10, int(base_transactions * (1 + transaction_variation)))
        
        # Randomly add some issues (10% chance of missing location)
        if random.random() < 0.1:
            country = None
            city = None
        else:
            country = random.choice(COUNTRIES)
            city = random.choice(CITIES)
        
        # For problematic merchants, ensure they maintain their issues
        if i in problematic_merchants:
            issue = problematic_merchants[i]
            if issue["type"] == "conversion_rate":
                conversion_rate = max(0.05, min(0.3, conversion_rate))  # Keep conversion rate low
            elif issue["type"] == "error_rate":
                error_rate = max(0.15, min(0.4, error_rate))  # Keep error rate high
            elif issue["type"] == "both":
                conversion_rate = max(0.05, min(0.25, conversion_rate))  # Keep conversion rate low
                error_rate = max(0.15, min(0.3, error_rate))  # Keep error rate high
        
        data_point = {
            "merchant_id": merchant_id,
            "merchant_name": merchant_name,
            "country": country,
            "city": city,
            "conversion_rate": round(conversion_rate, 4),
            "error_rate": round(error_rate, 4),
            "transaction_count": transaction_count,
            "timestamp": current_time.isoformat(),
            "status": random.choice(["active", "active", "active", "pending", "suspended"])
        }
        
        all_data.append(data_point)
    
    return all_data

def lambda_handler(event, context):
    """Lambda function handler"""
    try:
        logger.info("Starting hourly data generation...")
        
        # Generate hourly data
        data_points = generate_hourly_data()
        logger.info(f"Generated {len(data_points)} data points")
        
        # Create Elasticsearch client
        client = create_elasticsearch_client()
        
        # Check if index exists, create if not
        if not client.indices.exists(index=ELASTICSEARCH_INDEX):
            logger.info(f"Creating index {ELASTICSEARCH_INDEX}")
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
            client.indices.create(index=ELASTICSEARCH_INDEX, body=mapping)
        
        # Bulk insert data
        bulk_data = []
        for data_point in data_points:
            # Add index action
            bulk_data.append({"index": {"_index": ELASTICSEARCH_INDEX}})
            # Add document
            bulk_data.append(data_point)
        
        if bulk_data:
            response = client.bulk(body=bulk_data, refresh=True)
            
            # Check for errors
            if response.get("errors"):
                errors = [item for item in response["items"] if item.get("index", {}).get("error")]
                logger.error(f"Bulk insert errors: {errors}")
                return {
                    "statusCode": 500,
                    "body": json.dumps({
                        "message": "Some data points failed to insert",
                        "errors": errors
                    })
                }
            
            logger.info(f"Successfully inserted {len(data_points)} data points")
            
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": f"Successfully generated and inserted {len(data_points)} data points",
                    "timestamp": datetime.now().isoformat(),
                    "merchants_processed": len(data_points)
                })
            }
        else:
            logger.warning("No data points to insert")
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "No data points to insert",
                    "timestamp": datetime.now().isoformat()
                })
            }
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": f"Error generating data: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
        } 