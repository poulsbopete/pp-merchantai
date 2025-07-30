#!/bin/bash

echo "🐍 Setting up PayPal Merchant Troubleshooting with Python 3.11"
echo "=============================================================="

# Check if Python 3.11 is installed
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11 not found. Installing..."
    if command -v brew &> /dev/null; then
        brew install python@3.11
    else
        echo "❌ Homebrew not found. Please install Python 3.11 manually."
        exit 1
    fi
fi

# Remove existing venv if it exists
if [ -d "venv" ]; then
    echo "🗑️  Removing existing virtual environment..."
    rm -rf venv
fi

# Create new virtual environment with Python 3.11
echo "🔧 Creating virtual environment with Python 3.11..."
python3.11 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements-py311.txt

# Create .env file
echo "⚙️  Creating .env file..."
cat > .env << EOF
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USERNAME=
ELASTICSEARCH_PASSWORD=
ELASTICSEARCH_INDEX=paypal-merchants
DEBUG=true
EOF

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Start Elasticsearch: docker run -d --name elasticsearch -p 9200:9200 -e 'discovery.type=single-node' elasticsearch:8.11.0"
echo "2. Generate sample data: python scripts/generate_sample_data.py"
echo "3. Run the application: uvicorn app.main:app --reload"
echo "4. Access the dashboard: http://localhost:8000"
echo ""
echo "Remember to activate the virtual environment: source venv/bin/activate" 