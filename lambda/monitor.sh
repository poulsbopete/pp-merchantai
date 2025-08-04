#!/bin/bash

# Monitor Lambda function for hourly data generation
echo "🔍 Monitoring pp-merchantai-data-generator Lambda function..."

# Get function configuration
echo "📊 Function Configuration:"
aws lambda get-function --function-name pp-merchantai-data-generator --region us-east-1 --query 'Configuration.{FunctionName:FunctionName,Runtime:Runtime,Timeout:Timeout,MemorySize:MemorySize,LastModified:LastModified}' --output table

echo ""

# Get recent invocations
echo "📈 Recent Invocations (last 10):"
aws logs filter-log-events \
    --log-group-name /aws/lambda/pp-merchantai-data-generator \
    --start-time $(date -d '1 hour ago' +%s)000 \
    --query 'events[?contains(message, `Successfully inserted`)].{timestamp:timestamp,message:message}' \
    --output table

echo ""

# Get EventBridge rule status
echo "⏰ EventBridge Rule Status:"
aws events describe-rule --name pp-merchantai-hourly-data-generation --region us-east-1 --query '{Name:Name,ScheduleExpression:ScheduleExpression,State:State}' --output table

echo ""

# Get CloudWatch metrics (last 24 hours)
echo "📊 CloudWatch Metrics (last 24 hours):"
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value=pp-merchantai-data-generator \
    --start-time $(date -d '24 hours ago' -u +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 3600 \
    --statistics Sum \
    --region us-east-1 \
    --query 'Datapoints[].{Timestamp:Timestamp,Invocations:Sum}' \
    --output table

echo ""

# Check if function is working by testing a manual invocation
echo "🧪 Testing Manual Invocation:"
aws lambda invoke \
    --function-name pp-merchantai-data-generator \
    --payload '{}' \
    test-response.json \
    --region us-east-1

if [ $? -eq 0 ]; then
    echo "✅ Manual invocation successful"
    echo "📄 Response:"
    cat test-response.json | jq -r '.body' | jq .
    rm test-response.json
else
    echo "❌ Manual invocation failed"
fi

echo ""
echo "🎯 Monitoring complete!" 