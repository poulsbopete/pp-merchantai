# PayPal Merchant Troubleshooting App

A model context protocol application for analyzing and troubleshooting PayPal merchant issues using Elasticsearch.

## Features

- **Conversion Rate Analysis**: Identify merchants with conversion rate fluctuations
- **Location Data Validation**: Detect missing city/country information
- **Month-to-Month Comparisons**: Track performance trends over time
- **Error Rate Monitoring**: Identify merchants with >10% error fluctuations
- **Intelligent Troubleshooting**: AI-powered issue identification and recommendations

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   Create a `.env` file with your Elasticsearch configuration:
   ```
   ELASTICSEARCH_HOST=your-elasticsearch-host
   ELASTICSEARCH_PORT=9200
   ELASTICSEARCH_USERNAME=your-username
   ELASTICSEARCH_PASSWORD=your-password
   ELASTICSEARCH_INDEX=paypal-merchants
   ```

3. **Run the Application**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access the Dashboard**:
   Open your browser and navigate to `http://localhost:8000`

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