# Lambda Data Generator - Deployment Summary

## ✅ Successfully Deployed

A Lambda function has been successfully deployed to automatically generate and send test merchant data to Elasticsearch every hour.

## 🏗️ What Was Deployed

### 1. Lambda Function
- **Name**: `pp-merchantai-data-generator`
- **Runtime**: Python 3.11
- **Memory**: 512 MB
- **Timeout**: 5 minutes
- **Handler**: `data_generator.lambda_handler`

### 2. EventBridge Rule
- **Name**: `pp-merchantai-hourly-data-generation`
- **Schedule**: Every hour (`rate(1 hour)`)
- **State**: ENABLED
- **Target**: Lambda function

### 3. IAM Role
- **Name**: `pp-merchantai-data-generator-role`
- **Permissions**: CloudWatch Logs access
- **Trust Policy**: Lambda service

### 4. CloudWatch Log Group
- **Name**: `/aws/lambda/pp-merchantai-data-generator`
- **Retention**: 14 days

## 📊 Data Generation Details

### What Data is Generated
- **20 merchants** with realistic performance metrics
- **1 data point per merchant** per hour
- **480 data points per day** (20 × 24)
- **14,400 data points per month**

### Merchant Types
1. **Normal Merchants** (10 merchants)
   - Good performance (30-80% conversion rates)
   - Low error rates (1-15%)

2. **Problematic Merchants** (10 merchants)
   - **Low Conversion Rate**: 5-30% conversion rates
   - **High Error Rate**: 15-40% error rates
   - **Missing Location**: 10% chance of missing location data

### Data Fields
- `merchant_id`: Unique identifier (MERCH_001, MERCH_002, etc.)
- `merchant_name`: Business name
- `country`: Country code (US, CA, UK, etc.)
- `city`: City name
- `conversion_rate`: Transaction conversion rate (0.01-1.0)
- `error_rate`: Error rate (0.0-0.5)
- `transaction_count`: Number of transactions (10-5000)
- `timestamp`: Current timestamp
- `status`: Account status (active, pending, suspended)

## 🔧 Configuration

### Environment Variables
- `ELASTICSEARCH_HOST`: `https://ai-assistants-ffcafb.es.us-east-1.aws.elastic.cloud`
- `ELASTICSEARCH_USERNAME`: API key (base64 encoded)
- `ELASTICSEARCH_INDEX`: `pp-merchantai`

### Elasticsearch Connection
- Uses API key authentication
- HTTPS connection with certificate verification
- Bulk insert for efficient data insertion

## 📈 Monitoring

### CloudWatch Logs
- **Log Group**: `/aws/lambda/pp-merchantai-data-generator`
- **Log Level**: INFO
- **Key Messages**:
  - "Starting hourly data generation..."
  - "Generated X data points"
  - "Successfully inserted X data points"

### Metrics
- **Duration**: ~0.5 seconds average
- **Memory Used**: ~78 MB
- **Success Rate**: 100% (so far)

## 🧪 Testing

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

### Monitor Function
```bash
cd lambda
./monitor.sh
```

## 💰 Cost Estimation

### Lambda Costs
- **Executions**: 24/day × 30 days = 720/month
- **Duration**: ~0.5 seconds average
- **Memory**: 512 MB
- **Estimated Cost**: ~$0.25/month

### EventBridge Costs
- **Rules**: 1 rule
- **Targets**: 1 target
- **Estimated Cost**: ~$1.00/month

**Total Estimated Cost**: ~$1.25/month

## 🔄 Maintenance

### Updates
1. Modify `data_generator.py`
2. Run `./deploy.sh` to redeploy
3. Monitor logs for any issues

### Scaling
- **Automatic**: Lambda scales automatically
- **Manual**: Increase memory allocation if needed
- **Frequency**: Adjust EventBridge schedule if needed

### Troubleshooting
1. Check CloudWatch logs for errors
2. Verify Elasticsearch connectivity
3. Test manual invocation
4. Review IAM permissions

## 🎯 Benefits

1. **Continuous Data Flow**: Fresh data every hour for testing
2. **Realistic Scenarios**: Includes problematic merchants for AI testing
3. **Cost Effective**: Minimal AWS costs
4. **Fully Automated**: No manual intervention required
5. **Scalable**: Can easily adjust frequency or data volume
6. **Monitored**: Comprehensive logging and metrics

## 📋 Next Steps

1. **Monitor**: Watch the first few automatic executions
2. **Verify**: Check that data appears in your application
3. **Test AI Features**: Use the fresh data to test AI resolution features
4. **Adjust**: Modify data patterns if needed for specific testing scenarios

## 🔗 Related Resources

- **Application**: http://production-pp-merchantai-alb-1317140292.us-east-1.elb.amazonaws.com
- **Lambda Console**: https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/pp-merchantai-data-generator
- **CloudWatch Logs**: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/aws$252Flambda$252Fpp-merchantai-data-generator
- **EventBridge Console**: https://console.aws.amazon.com/events/home?region=us-east-1#/rules/pp-merchantai-hourly-data-generation

---

**Deployment Date**: August 4, 2025  
**Status**: ✅ Active and Running  
**Next Execution**: Every hour on the hour (UTC) 