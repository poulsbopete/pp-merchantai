#!/usr/bin/env python3
"""
Quick Test Script
Tests the application once we have proper Elastic Cloud authentication.
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()

def test_connection():
    """Test Elasticsearch connection"""
    try:
        from app.elastic_client import ElasticClient
        client = ElasticClient()
        
        # Test basic connection
        info = client.client.info()
        print(f"✅ Connected to Elasticsearch: {info['cluster_name']}")
        
        # Test index creation
        index_name = os.getenv("ELASTICSEARCH_INDEX", "paypal-merchants")
        if not client.client.indices.exists(index=index_name):
            client.client.indices.create(index=index_name)
            print(f"✅ Created index: {index_name}")
        else:
            print(f"✅ Index exists: {index_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_sample_data():
    """Test sample data generation"""
    try:
        from scripts.generate_sample_data import generate_sample_data
        generate_sample_data()
        print("✅ Sample data generated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Sample data generation failed: {e}")
        return False

def test_app_startup():
    """Test FastAPI app startup"""
    try:
        from app.main import app
        print("✅ FastAPI app imports successfully")
        return True
        
    except Exception as e:
        print(f"❌ App startup failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Quick Test Suite")
    print("=" * 40)
    
    # Test connection
    print("\n1. Testing Elasticsearch connection...")
    connection_ok = test_connection()
    
    if connection_ok:
        # Test sample data
        print("\n2. Testing sample data generation...")
        data_ok = test_sample_data()
        
        # Test app
        print("\n3. Testing app startup...")
        app_ok = test_app_startup()
        
        if data_ok and app_ok:
            print("\n🎉 All tests passed! Your app is ready to run.")
            print("\nTo start the application:")
            print("uvicorn app.main:app --reload")
            print("\nThen visit: http://localhost:8000")
        else:
            print("\n⚠️  Some tests failed. Check the errors above.")
    else:
        print("\n❌ Connection failed. Please check your Elastic Cloud credentials.")
        print("\nMake sure your .env file has the correct:")
        print("- ELASTICSEARCH_HOST")
        print("- ELASTICSEARCH_USERNAME (API key or username)")
        print("- ELASTICSEARCH_PASSWORD (if using username/password auth)")

if __name__ == "__main__":
    main() 