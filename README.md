# PayPal Merchant Troubleshooting App

A model context protocol application for analyzing and troubleshooting PayPal merchant issues using Elasticsearch.

## Features

- **Conversion Rate Analysis**: Identify merchants with conversion rate fluctuations
- **Location Data Validation**: Detect missing city/country information
- **Month-to-Month Comparisons**: Track performance trends over time
- **Error Rate Monitoring**: Identify merchants with >10% error fluctuations
- **AI-Powered Location Resolution**: Automatically resolve missing city/country data using LLM
- **AI-Generated Insights**: Get personalized troubleshooting recommendations for merchants
- **Multi-LLM Support**: OpenAI (GPT-4) and Anthropic (Claude) integration
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

**For Local Elasticsearch:**
```bash
# Create .env file for local Elasticsearch
cat > .env << EOF
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USERNAME=
ELASTICSEARCH_PASSWORD=
ELASTICSEARCH_INDEX=paypal-merchants
DEBUG=true
EOF
```

**For Elastic Cloud:**
```bash
# Create .env file for Elastic Cloud
cat > .env << EOF
ELASTICSEARCH_HOST=https://your-deployment.es.us-east-1.aws.elastic.cloud
ELASTICSEARCH_PORT=443
ELASTICSEARCH_USERNAME=your-api-key-base64-encoded
ELASTICSEARCH_PASSWORD=
ELASTICSEARCH_INDEX=paypal-merchants
DEBUG=true
EOF
```

### 4. Set Up Elasticsearch

**For Local Elasticsearch:**
```bash
# Start Elasticsearch with Docker
docker run -d --name elasticsearch -p 9200:9200 -e 'discovery.type=single-node' elasticsearch:8.11.0

# Wait for Elasticsearch to be ready (about 30 seconds)
curl http://localhost:9200
```

**For Elastic Cloud:**
```bash
# Set up Elastic Cloud connection and create index
python scripts/setup_elastic_cloud.py
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
- `POST /api/ai/resolve-locations`: AI-powered location resolution
- `GET /api/ai/insights/{merchant_id}`: AI-generated merchant insights
- `GET /api/ai/status`: AI agent status and capabilities

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

## AI Features

### LLM Integration Setup

The application includes AI-powered features for automated location resolution and merchant insights. Configure LLM providers in your `.env` file:

**For OpenAI (GPT-4):**
```bash
# Add to your .env file
OPENAI_API_KEY=your-openai-api-key-here
LLM_MODEL=gpt-4
```

            **For Anthropic (Claude):**
            ```bash
            # Add to your .env file
            ANTHROPIC_API_KEY=your-anthropic-api-key-here
            LLM_MODEL=claude-3-sonnet-20240229
            ```
            
            **Demo Mode (Recommended for Testing):**
            ```bash
            # Add to your .env file to avoid API throttling
            DEMO_MODE=true
            ```
            *Demo mode uses cached responses and fallback recommendations to avoid API rate limits*

### AI Capabilities

1. **Automated Location Resolution**
   - AI analyzes business names to predict missing city/country data
   - Automatic updates to Elasticsearch with resolved locations
   - Confidence scoring for each resolution
   - Fallback to rule-based resolution if no API key

2. **AI-Generated Insights**
   - Personalized troubleshooting recommendations for each merchant
   - Analysis of conversion rates, error rates, and performance patterns
   - Actionable optimization strategies

3. **Web Dashboard Integration**
   - One-click AI location resolution
   - Real-time AI status monitoring
   - Interactive results display with confidence scores

### Testing AI Features

```bash
# Test AI features (works with or without API keys)
python scripts/test_ai_features.py

# The app works in two modes:
# - Without API keys: Uses rule-based resolution and basic insights
# - With API keys: Full AI-powered analysis and recommendations
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

**Python 3.13 Compatibility Issues:**
If you encounter pydantic-core compilation errors with Python 3.13:
```bash
# Option 1: Use Python 3.11 (Recommended)
brew install python@3.11
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements-py311.txt

# Option 2: Try with updated requirements
pip install -r requirements.txt

# Option 3: Install pre-compiled wheels
pip install --only-binary=all -r requirements.txt
```

**Docker Issues:**
```bash
# Make sure Docker is running
docker --version

# If using Docker Compose, try:
docker-compose down
docker-compose up -d
``` 