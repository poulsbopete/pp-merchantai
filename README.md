# PayPal Merchant Troubleshooting App

A model context protocol application for analyzing and troubleshooting PayPal merchant issues using Elasticsearch.

## Features

- **Conversion Rate Analysis**: Identify merchants with conversion rate fluctuations
- **Location Data Validation**: Detect missing city/country information
- **Month-to-Month Comparisons**: Track performance trends over time
- **Error Rate Monitoring**: Identify merchants with >10% error fluctuations
- **Intelligent Troubleshooting**: AI-powered issue identification and recommendations

## Quick Start

### Prerequisites
- Python 3.11+ 
- Docker (for Elasticsearch)
- Git

### 1. Set Up Virtual Environment

**macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify activation (you should see (venv) in your prompt)
which python
```

**Windows:**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
# Make sure your virtual environment is activated
pip install -r requirements.txt
```

### 3. Set Environment Variables
Create a `.env` file with your Elasticsearch configuration:
```bash
# Create .env file
cat > .env << EOF
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USERNAME=
ELASTICSEARCH_PASSWORD=
ELASTICSEARCH_INDEX=paypal-merchants
DEBUG=true
EOF
```

### 4. Start Elasticsearch
```bash
# Start Elasticsearch with Docker
docker run -d --name elasticsearch -p 9200:9200 -e 'discovery.type=single-node' elasticsearch:8.11.0

# Wait for Elasticsearch to be ready (about 30 seconds)
curl http://localhost:9200
```

### 5. Generate Sample Data
```bash
python scripts/generate_sample_data.py
```

### 6. Run the Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Access the Dashboard
Open your browser and navigate to `http://localhost:8000`

### Alternative: Docker Compose (Easiest)
If you prefer to run everything with Docker:
```bash
# Start the entire stack
docker-compose up -d

# Access the application
open http://localhost:8000
```

## API Endpoints

- `GET /`: Main dashboard
- `GET /api/merchants`: Get all merchants
- `GET /api/merchants/{merchant_id}`: Get specific merchant details
- `GET /api/analytics/conversion-rates`: Conversion rate analysis
- `GET /api/analytics/location-issues`: Missing location data
- `GET /api/analytics/monthly-comparison`: Month-to-month comparison
- `POST /api/troubleshoot`: AI-powered troubleshooting

## Data Structure

The app expects Elasticsearch documents with the following structure:
```json
{
  "merchant_id": "string",
  "merchant_name": "string",
  "country": "string",
  "city": "string",
  "conversion_rate": "float",
  "error_rate": "float",
  "transaction_count": "integer",
  "timestamp": "datetime",
  "status": "string"
}
```

## Troubleshooting Features

1. **Conversion Rate Issues**: Identifies merchants with significant conversion rate drops
2. **Location Data Gaps**: Finds merchants missing city or country information
3. **Error Rate Spikes**: Detects merchants with >10% error fluctuations
4. **Trend Analysis**: Provides month-to-month performance comparisons
5. **AI Recommendations**: Suggests actions based on identified issues

## Troubleshooting

### macOS Issues

**"externally-managed-environment" Error:**
```bash
# This is expected on macOS. Always use a virtual environment:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Elasticsearch Connection Issues:**
```bash
# Check if Elasticsearch is running
curl http://localhost:9200

# If not running, start it:
docker run -d --name elasticsearch -p 9200:9200 -e 'discovery.type=single-node' elasticsearch:8.11.0

# Wait for it to be ready (about 30 seconds)
```

**Port Already in Use:**
```bash
# Check what's using port 8000
lsof -i :8000

# Kill the process if needed
kill -9 <PID>
```

### General Issues

**Virtual Environment Not Activated:**
```bash
# You should see (venv) in your prompt
# If not, activate it:
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows
```

**Dependencies Installation Failed:**
```bash
# Upgrade pip first
pip install --upgrade pip

# Then install requirements
pip install -r requirements.txt
```

**Docker Issues:**
```bash
# Make sure Docker is running
docker --version

# If using Docker Compose, try:
docker-compose down
docker-compose up -d
``` 