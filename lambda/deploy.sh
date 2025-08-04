#!/bin/bash

# Deploy Lambda function for hourly data generation
set -e

echo "🚀 Deploying Lambda function for hourly data generation..."

# Create deployment directory
DEPLOY_DIR="deployment"
rm -rf $DEPLOY_DIR
mkdir -p $DEPLOY_DIR

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt -t $DEPLOY_DIR

# Copy Lambda function code
echo "📝 Copying Lambda function code..."
cp data_generator.py $DEPLOY_DIR/

# Create deployment package
echo "📦 Creating deployment package..."
cd $DEPLOY_DIR
zip -r ../lambda-deployment.zip .
cd ..

# Deploy using AWS CLI
echo "☁️ Deploying to AWS..."

# Create the stack
aws cloudformation deploy \
    --template-file cloudformation.yml \
    --stack-name pp-merchantai-data-generator \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
        ElasticsearchHost=https://ai-assistants-ffcafb.es.us-east-1.aws.elastic.cloud \
        ElasticsearchUsername=VFpHZFpwZ0JuckxKTnZGLTF5SE46dFpMNGxfV3pEbVJYZTFRZHRNZkg4UQ== \
        ElasticsearchIndex=pp-merchantai \
    --region us-east-1

# Update the Lambda function code
echo "🔄 Updating Lambda function code..."
FUNCTION_NAME=$(aws cloudformation describe-stacks \
    --stack-name pp-merchantai-data-generator \
    --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionName`].OutputValue' \
    --output text \
    --region us-east-1)

aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://lambda-deployment.zip \
    --region us-east-1

# Clean up
echo "🧹 Cleaning up..."
rm -rf $DEPLOY_DIR
rm lambda-deployment.zip

echo "✅ Deployment complete!"
echo "📊 Lambda function: $FUNCTION_NAME"
echo "⏰ Scheduled to run every hour via EventBridge"
echo "📝 Check CloudWatch logs for execution details" 