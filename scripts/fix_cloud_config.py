#!/usr/bin/env python3
"""
Fix Elastic Cloud Configuration
This script helps fix the Cloud ID format and update the .env file.
"""

import os
from dotenv import load_dotenv

load_dotenv()

def main():
    print("🔧 Fixing Elastic Cloud Configuration")
    print("=" * 50)
    print()
    
    # Get current values
    current_cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
    current_username = os.getenv("ELASTICSEARCH_USERNAME")
    current_password = os.getenv("ELASTICSEARCH_PASSWORD")
    current_index = os.getenv("ELASTICSEARCH_INDEX")
    
    print("Current configuration:")
    print(f"Cloud ID: {current_cloud_id}")
    print(f"Username: {current_username[:20] if current_username else 'Not set'}...")
    print(f"Password: {'Set' if current_password else 'Not set'}")
    print(f"Index: {current_index}")
    print()
    
    # The issue is that you put the full URL in CLOUD_ID
    # Cloud ID should be in format: deployment-name:base64-encoded-endpoint
    if current_cloud_id and current_cloud_id.startswith("https://"):
        print("❌ Issue detected: You put the full URL in CLOUD_ID field")
        print()
        print("The correct format should be:")
        print("ELASTICSEARCH_CLOUD_ID=ai-assistants:...")
        print()
        print("To get the correct Cloud ID:")
        print("1. Go to your Elastic Cloud console")
        print("2. Select your deployment")
        print("3. Click 'Copy endpoint'")
        print("4. Copy the 'Cloud ID' value (not the URL)")
        print()
        print("For now, let's use the direct endpoint approach:")
        print()
        
        # Create corrected .env content
        env_content = f"""# Elastic Cloud Configuration
ELASTICSEARCH_HOST={current_cloud_id}
ELASTICSEARCH_PORT=443
ELASTICSEARCH_USERNAME={current_username}
ELASTICSEARCH_PASSWORD={current_password or ''}
ELASTICSEARCH_INDEX={current_index or 'paypal-merchants'}
DEBUG=true
"""
        
        print("Updated .env content:")
        print("-" * 30)
        print(env_content)
        print("-" * 30)
        
        # Write the corrected .env file
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ .env file updated with correct format!")
        print("Now try running: python scripts/test_elastic_cloud.py")
        
    else:
        print("✅ Configuration looks correct!")
        print("Try running: python scripts/test_elastic_cloud.py")

if __name__ == "__main__":
    main() 