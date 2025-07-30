#!/usr/bin/env python3
"""
Demo script for PayPal Merchant Troubleshooting App
This script sets up the environment and runs the application with sample data.
"""

import os
import sys
import subprocess
import time
import requests
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_elasticsearch():
    """Check if Elasticsearch is running"""
    try:
        response = requests.get("http://localhost:9200", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Elasticsearch is running")
            return True
    except requests.exceptions.RequestException:
        pass
    
    logger.error("❌ Elasticsearch is not running")
    logger.info("Please start Elasticsearch first:")
    logger.info("  - Docker: docker run -d --name elasticsearch -p 9200:9200 -e 'discovery.type=single-node' elasticsearch:8.11.0")
    logger.info("  - Or install and start Elasticsearch locally")
    return False

def install_dependencies():
    """Install Python dependencies"""
    try:
        logger.info("Installing Python dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        logger.info("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        return False

def generate_sample_data():
    """Generate sample data for the demo"""
    try:
        logger.info("Generating sample data...")
        script_path = Path(__file__).parent / "generate_sample_data.py"
        subprocess.run([sys.executable, str(script_path)], check=True)
        logger.info("✅ Sample data generated successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to generate sample data: {e}")
        return False

def start_application():
    """Start the FastAPI application"""
    try:
        logger.info("Starting the application...")
        logger.info("🌐 Application will be available at: http://localhost:8000")
        logger.info("📚 API documentation will be available at: http://localhost:8000/docs")
        logger.info("Press Ctrl+C to stop the application")
        
        # Start the application
        subprocess.run([sys.executable, "-m", "uvicorn", "app.main:app", 
                       "--host", "0.0.0.0", "--port", "8000", "--reload"])
    except KeyboardInterrupt:
        logger.info("\n🛑 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")

def wait_for_elasticsearch():
    """Wait for Elasticsearch to be ready"""
    logger.info("Waiting for Elasticsearch to be ready...")
    for i in range(30):  # Wait up to 30 seconds
        if check_elasticsearch():
            return True
        time.sleep(1)
    return False

def main():
    """Main demo function"""
    logger.info("🚀 Starting PayPal Merchant Troubleshooting Demo")
    logger.info("=" * 50)
    
    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        logger.error("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Step 1: Check Elasticsearch
    if not wait_for_elasticsearch():
        sys.exit(1)
    
    # Step 2: Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Step 3: Generate sample data
    if not generate_sample_data():
        sys.exit(1)
    
    # Step 4: Start application
    start_application()

if __name__ == "__main__":
    main() 