#!/usr/bin/env python3
"""
Get Elastic Cloud Connection Information
This script helps you get the correct connection details from your Elastic Cloud deployment.
"""

import os
from dotenv import load_dotenv

load_dotenv()

def main():
    print("🔍 Elastic Cloud Connection Information")
    print("=" * 50)
    print()
    print("To get the correct connection details:")
    print()
    print("1. Go to your Elastic Cloud console:")
    print("   https://cloud.elastic.co/")
    print()
    print("2. Select your deployment: ai-assistants-ffcafb")
    print()
    print("3. Go to 'Copy endpoint' and copy the connection details")
    print()
    print("4. You should see something like:")
    print("   Cloud ID: ai-assistants:...")
    print("   Elasticsearch endpoint: https://...")
    print()
    print("5. For API Keys:")
    print("   - Go to 'Security' → 'API Keys'")
    print("   - Create a new API key with these permissions:")
    print("     * cluster_monitor")
    print("     * manage_index_templates") 
    print("     * manage_ilm")
    print("     * monitor")
    print("     * read")
    print("     * write")
    print()
    print("6. Update your .env file with the new credentials")
    print()
    print("Current .env configuration:")
    print(f"Host: {os.getenv('ELASTICSEARCH_HOST', 'Not set')}")
    print(f"Port: {os.getenv('ELASTICSEARCH_PORT', 'Not set')}")
    print(f"Username: {os.getenv('ELASTICSEARCH_USERNAME', 'Not set')[:20] if os.getenv('ELASTICSEARCH_USERNAME') else 'Not set'}...")
    print(f"Password: {'Set' if os.getenv('ELASTICSEARCH_PASSWORD') else 'Not set'}")
    print(f"Index: {os.getenv('ELASTICSEARCH_INDEX', 'Not set')}")

if __name__ == "__main__":
    main() 