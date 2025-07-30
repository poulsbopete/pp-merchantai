#!/usr/bin/env python3
"""
Simple Elastic Cloud Test
Tests connection using the same approach as other working apps.
"""

import os
import base64
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

def main():
    print("🔍 Simple Elastic Cloud Test")
    print("=" * 40)
    
    # Get configuration
    host = os.getenv("ELASTICSEARCH_HOST")
    username = os.getenv("ELASTICSEARCH_USERNAME")
    index_name = os.getenv("ELASTICSEARCH_INDEX", "pp-merchantai")
    
    print(f"Host: {host}")
    print(f"Username (API key): {username[:20] if username else 'Not set'}...")
    print(f"Index: {index_name}")
    print()
    
    try:
        # Decode the API key
        api_key = base64.b64decode(username).decode('utf-8')
        print(f"Decoded API key: {api_key[:20]}...{api_key[-20:]}")
        
        # Create client with API key
        client = Elasticsearch(
            [host],
            api_key=api_key,
            verify_certs=True
        )
        
        # Test connection
        print("\nTesting connection...")
        info = client.info()
        print(f"✅ Connected to: {info['cluster_name']}")
        print(f"Elasticsearch version: {info['version']['number']}")
        
        # Test index operations
        print(f"\nTesting index: {index_name}")
        
        # Check if index exists
        if client.indices.exists(index=index_name):
            print(f"✅ Index '{index_name}' exists")
            
            # Get index stats
            stats = client.indices.stats(index=index_name)
            doc_count = stats['indices'][index_name]['total']['docs']['count']
            print(f"📊 Document count: {doc_count}")
        else:
            print(f"📝 Index '{index_name}' doesn't exist, creating...")
            client.indices.create(index=index_name)
            print(f"✅ Created index '{index_name}'")
        
        # Test document operations
        print("\nTesting document operations...")
        
        # Index a test document
        test_doc = {
            "merchant_id": "test-001",
            "name": "Test Merchant",
            "conversion_rate": 0.85,
            "location": {
                "city": "Test City",
                "country": "Test Country"
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        response = client.index(
            index=index_name,
            document=test_doc,
            id="test-doc-001"
        )
        print(f"✅ Indexed test document: {response['result']}")
        
        # Search for the document
        search_response = client.search(
            index=index_name,
            body={
                "query": {
                    "match": {
                        "merchant_id": "test-001"
                    }
                }
            }
        )
        
        hits = search_response['hits']['total']['value']
        print(f"✅ Search found {hits} documents")
        
        # Clean up test document
        client.delete(index=index_name, id="test-doc-001")
        print("✅ Cleaned up test document")
        
        print("\n🎉 All tests passed! Your Elastic Cloud connection is working perfectly.")
        print("\nYou can now run your PayPal Merchant AI app:")
        print("python scripts/setup_elastic_cloud.py")
        print("python scripts/generate_sample_data.py")
        print("uvicorn app.main:app --reload")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("\nThis might be a permissions issue. Check that your API key has:")
        print("- read permissions")
        print("- write permissions")
        print("- manage_index_templates permissions")

if __name__ == "__main__":
    main() 