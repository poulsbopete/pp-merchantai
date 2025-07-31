#!/bin/bash

# PayPal Merchant AI - AWS Deployment Script
set -e

# Configuration
ENVIRONMENT=${1:-production}
REGION=${2:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY="pp-merchantai"
STACK_NAME="${ENVIRONMENT}-pp-merchantai"

echo "🚀 Deploying PayPal Merchant AI to AWS"
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "Account ID: $ACCOUNT_ID"
echo "Stack Name: $STACK_NAME"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Check if Podman is available, fallback to Docker
if command -v podman &> /dev/null; then
    CONTAINER_ENGINE="podman"
    echo "🐳 Using Podman as container engine"
elif command -v docker &> /dev/null; then
    CONTAINER_ENGINE="docker"
    echo "🐳 Using Docker as container engine"
else
    echo "❌ Neither Podman nor Docker found. Please install one of them."
    exit 1
fi

# Create ECR repository if it doesn't exist
echo "📦 Setting up ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $REGION > /dev/null 2>&1 || {
    echo "Creating ECR repository: $ECR_REPOSITORY"
    aws ecr create-repository --repository-name $ECR_REPOSITORY --region $REGION
}

# Get ECR login token
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $REGION | $CONTAINER_ENGINE login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Build and push container image
echo "🐳 Building and pushing container image..."
$CONTAINER_ENGINE build -f Dockerfile.prod -t $ECR_REPOSITORY .
$CONTAINER_ENGINE tag $ECR_REPOSITORY:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPOSITORY:latest
$CONTAINER_ENGINE push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPOSITORY:latest

# Create secrets in AWS Secrets Manager
echo "🔒 Setting up secrets..."
aws secretsmanager describe-secret --secret-id "pp-merchantai/openai-api-key" --region $REGION > /dev/null 2>&1 || {
    echo "Creating OpenAI API key secret..."
    aws secretsmanager create-secret \
        --name "pp-merchantai/openai-api-key" \
        --description "OpenAI API key for PayPal Merchant AI" \
        --secret-string "your-openai-api-key-here" \
        --region $REGION
}

aws secretsmanager describe-secret --secret-id "pp-merchantai/anthropic-api-key" --region $REGION > /dev/null 2>&1 || {
    echo "Creating Anthropic API key secret..."
    aws secretsmanager create-secret \
        --name "pp-merchantai/anthropic-api-key" \
        --description "Anthropic API key for PayPal Merchant AI" \
        --secret-string "your-anthropic-api-key-here" \
        --region $REGION
}

# Update CloudFormation template with actual values
echo "📝 Preparing CloudFormation template..."
sed -i.bak "s/ACCOUNT_ID/$ACCOUNT_ID/g" aws/ecs-task-definition.json
sed -i.bak "s/REGION/$REGION/g" aws/ecs-task-definition.json
sed -i.bak "s/ELASTICSEARCH_HOST_PLACEHOLDER/$ELASTICSEARCH_HOST/g" aws/ecs-task-definition.json
sed -i.bak "s/ELASTICSEARCH_USERNAME_PLACEHOLDER/$ELASTICSEARCH_USERNAME/g" aws/ecs-task-definition.json

# Deploy CloudFormation stack
echo "☁️ Deploying CloudFormation stack..."
aws cloudformation deploy \
    --template-file aws/cloudformation-template.yml \
    --stack-name $STACK_NAME \
    --parameter-overrides Environment=$ENVIRONMENT \
    --capabilities CAPABILITY_NAMED_IAM \
    --region $REGION

# Get stack outputs
echo "📊 Getting deployment outputs..."
ALB_DNS=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
    --output text)

CLOUDFRONT_DOMAIN=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDomain`].OutputValue' \
    --output text)

echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Application URLs:"
echo "   Load Balancer: http://$ALB_DNS"
echo "   CloudFront: https://$CLOUDFRONT_DOMAIN"
echo ""
echo "📋 Next steps:"
echo "   1. Update your Elasticsearch credentials in AWS Systems Manager Parameter Store"
echo "   2. Update API keys in AWS Secrets Manager"
echo "   3. Test the application at: https://$CLOUDFRONT_DOMAIN"
echo ""
echo "🔧 Useful commands:"
echo "   View logs: aws logs tail /ecs/$ENVIRONMENT-pp-merchantai --region $REGION"
echo "   Update secrets: aws secretsmanager update-secret --secret-id pp-merchantai/openai-api-key --secret-string 'your-new-key' --region $REGION"
echo "   Scale service: aws ecs update-service --cluster $ENVIRONMENT-pp-merchantai-cluster --service $ENVIRONMENT-pp-merchantai-service --desired-count 3 --region $REGION" 