# Lambda Data Generator

This Lambda function automatically generates and sends test merchant data to Elasticsearch every hour.

## Overview

The Lambda function generates realistic merchant data including:
- 20 different merchants with varying performance metrics
- Conversion rates, error rates, and transaction counts
- Location data (with some merchants having missing location data for testing)
- Timestamped data points for trend analysis

## Features

- **Hourly Execution**: Runs every hour via EventBridge
- **Realistic Data**: Generates data with realistic variations and issues
- **Problematic Merchants**: Includes merchants with specific issues for testing AI resolution
- **Bulk Insert**: Efficiently inserts data using Elasticsearch bulk API
- **Error Handling**: Comprehensive error handling and logging
- **Auto-scaling**: Automatically scales based on load

## Data Generated

### Merchant Types
- **Normal Merchants**: Good performance (30-80% conversion rates, 1-15% error rates)
- **Problematic Merchants**: Specific issues for testing:
  - Low conversion rates (5-30%)
  - High error rates (15-40%)
  - Missing location data (10% chance per merchant)

### Data Points Per Hour
- 20 merchants × 1 data point = 20 total data points per hour
- 480 data points per day
- 14,400 data points per month

## Deployment

### Prerequisites
- AWS CLI configured with appropriate permissions
- Python 3.11
- Access to Elasticsearch Cloud instance

### Quick Deploy
```bash
cd lambda
./deploy.sh
```

### Manual Deployment
1. Install dependencies:
   ```bash
   pip install -r requirements.txt -t deployment/
   ```

2. Copy Lambda function:
   ```bash
   cp data_generator.py deployment/
   ```

3. Create deployment package:
   ```bash
   cd deployment
   zip -r ../lambda-deployment.zip .
   cd ..
   ```

4. Deploy CloudFormation stack:
   ```bash
   aws cloudformation deploy \
       --template-file cloudformation.yml \
       --stack-name pp-merchantai-data-generator \
       --capabilities CAPABILITY_NAMED_IAM \
       --region us-east-1
   ```

5. Update Lambda function code:
   ```bash
   aws lambda update-function-code \
       --function-name pp-merchantai-data-generator \
       --zip-file fileb://lambda-deployment.zip \
       --region us-east-1
   ```

## Configuration

### Environment Variables
- `ELASTICSEARCH_HOST`: Elasticsearch Cloud endpoint
- `ELASTICSEARCH_USERNAME`: API key (base64 encoded)
- `ELASTICSEARCH_INDEX`: Index name (default: pp-merchantai)

### Scheduling
The function is scheduled to run every hour using EventBridge:
- **Schedule**: `rate(1 hour)`
- **Timezone**: UTC
- **Retry**: Automatic retry on failure

## Monitoring

### CloudWatch Logs
- **Log Group**: `/aws/lambda/pp-merchantai-data-generator`
- **Retention**: 14 days
- **Log Level**: INFO

### Metrics
- **Duration**: Expected 5-30 seconds
- **Memory**: 512 MB allocated
- **Timeout**: 5 minutes

## Testing

### Manual Invocation
```bash
aws lambda invoke \
    --function-name pp-merchantai-data-generator \
    --payload '{}' \
    response.json
```

### Check Logs
```bash
aws logs tail /aws/lambda/pp-merchantai-data-generator --follow
```

## Troubleshooting

### Common Issues
1. **Elasticsearch Connection**: Check API key and host URL
2. **Index Creation**: Ensure proper permissions for index creation
3. **Bulk Insert Errors**: Check data format and Elasticsearch mapping
4. **Timeout**: Increase timeout if processing large datasets

### Debug Mode
Enable debug logging by modifying the Lambda function:
```python
logger.setLevel(logging.DEBUG)
```

## Cost Estimation

### Lambda Costs
- **Executions**: 24 per day × 30 days = 720 executions/month
- **Duration**: ~10 seconds average
- **Memory**: 512 MB
- **Estimated Cost**: ~$0.50/month

### EventBridge Costs
- **Rules**: 1 rule
- **Targets**: 1 target
- **Estimated Cost**: ~$1.00/month

**Total Estimated Cost**: ~$1.50/month

## Security

### IAM Permissions
- CloudWatch Logs access
- Lambda execution role
- No external network access required (uses Elasticsearch Cloud)

### Data Security
- API key stored as environment variable
- No sensitive data in logs
- HTTPS communication with Elasticsearch

## Maintenance

### Updates
1. Modify `data_generator.py`
2. Run `./deploy.sh` to redeploy
3. Monitor logs for any issues

### Scaling
- **Automatic**: Lambda scales automatically
- **Manual**: Increase memory allocation if needed
- **Frequency**: Adjust EventBridge schedule if needed

## Support

For issues or questions:
1. Check CloudWatch logs first
2. Verify Elasticsearch connectivity
3. Test manual invocation
4. Review IAM permissions 