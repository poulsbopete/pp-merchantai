# AWS Deployment Guide for PayPal Merchant AI

This guide will help you deploy the PayPal Merchant AI application to AWS using CloudFront, ECS, and other AWS services.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CloudFront    │    │   Application   │    │   ECS Fargate   │
│   Distribution  │───▶│   Load Balancer │───▶│   Containers    │
│   (CDN)         │    │   (ALB)         │    │   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   S3 Bucket     │    │   VPC +         │    │   Elastic Cloud │
│   (Static Assets)│   │   Security      │    │   (Serverless)  │
│                 │   │   Groups        │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

1. **AWS CLI** installed and configured
2. **Docker** installed
3. **AWS Account** with appropriate permissions
4. **Elastic Cloud** instance (already configured)

## 🚀 Quick Deployment

### 1. Set Environment Variables

```bash
# Set your Elastic Cloud credentials
export ELASTICSEARCH_HOST="https://your-elastic-cloud-instance.es.us-east-1.aws.elastic.cloud"
export ELASTICSEARCH_USERNAME="your-base64-encoded-api-key"

# Optional: Set AWS region
export AWS_DEFAULT_REGION="us-east-1"
```

### 2. Run Deployment Script

```bash
# Deploy to production
./aws/deploy.sh production us-east-1

# Or deploy to staging
./aws/deploy.sh staging us-east-1
```

## 🔧 Manual Deployment Steps

If you prefer to deploy manually, follow these steps:

### 1. Create ECR Repository

```bash
aws ecr create-repository --repository-name pp-merchantai --region us-east-1
```

### 2. Build and Push Docker Image

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -f Dockerfile.prod -t pp-merchantai .

# Tag and push
docker tag pp-merchantai:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pp-merchantai:latest
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pp-merchantai:latest
```

### 3. Create Secrets

```bash
# Create OpenAI API key secret
aws secretsmanager create-secret \
    --name "pp-merchantai/openai-api-key" \
    --description "OpenAI API key for PayPal Merchant AI" \
    --secret-string "your-openai-api-key-here" \
    --region us-east-1

# Create Anthropic API key secret
aws secretsmanager create-secret \
    --name "pp-merchantai/anthropic-api-key" \
    --description "Anthropic API key for PayPal Merchant AI" \
    --secret-string "your-anthropic-api-key-here" \
    --region us-east-1
```

### 4. Deploy CloudFormation Stack

```bash
aws cloudformation deploy \
    --template-file aws/cloudformation-template.yml \
    --stack-name production-pp-merchantai \
    --parameter-overrides Environment=production \
    --capabilities CAPABILITY_NAMED_IAM \
    --region us-east-1
```

## 🌐 Accessing Your Application

After deployment, you'll get two URLs:

1. **Load Balancer URL**: Direct access to the ALB
2. **CloudFront URL**: CDN-accelerated access (recommended)

### Get URLs

```bash
# Get Load Balancer DNS
aws cloudformation describe-stacks \
    --stack-name production-pp-merchantai \
    --region us-east-1 \
    --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
    --output text

# Get CloudFront domain
aws cloudformation describe-stacks \
    --stack-name production-pp-merchantai \
    --region us-east-1 \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDomain`].OutputValue' \
    --output text
```

## 🔍 Monitoring and Logs

### View Application Logs

```bash
aws logs tail /ecs/production-pp-merchantai --region us-east-1 --follow
```

### Check ECS Service Status

```bash
aws ecs describe-services \
    --cluster production-pp-merchantai-cluster \
    --services production-pp-merchantai-service \
    --region us-east-1
```

### Monitor CloudWatch Metrics

- Go to AWS CloudWatch console
- Navigate to "Metrics" → "ECS/ContainerInsights"
- Select your cluster and service

## 🔧 Configuration Updates

### Update API Keys

```bash
# Update OpenAI API key
aws secretsmanager update-secret \
    --secret-id pp-merchantai/openai-api-key \
    --secret-string "your-new-openai-key" \
    --region us-east-1

# Update Anthropic API key
aws secretsmanager update-secret \
    --secret-id pp-merchantai/anthropic-api-key \
    --secret-string "your-new-anthropic-key" \
    --region us-east-1
```

### Scale the Application

```bash
# Scale to 3 instances
aws ecs update-service \
    --cluster production-pp-merchantai-cluster \
    --service production-pp-merchantai-service \
    --desired-count 3 \
    --region us-east-1
```

### Update Environment Variables

```bash
# Update task definition with new environment variables
aws ecs register-task-definition \
    --cli-input-json file://aws/ecs-task-definition.json \
    --region us-east-1

# Update service to use new task definition
aws ecs update-service \
    --cluster production-pp-merchantai-cluster \
    --service production-pp-merchantai-service \
    --task-definition production-pp-merchantai:REVISION \
    --region us-east-1
```

## 🛡️ Security Features

- **VPC**: Isolated network environment
- **Security Groups**: Restrictive firewall rules
- **IAM Roles**: Least privilege access
- **Secrets Manager**: Secure credential storage
- **HTTPS**: Encrypted traffic via CloudFront
- **WAF**: Web Application Firewall (can be added)

## 💰 Cost Optimization

### Estimated Monthly Costs (us-east-1)

- **ECS Fargate**: ~$30-50/month (2 instances)
- **Application Load Balancer**: ~$20/month
- **CloudFront**: ~$5-10/month
- **CloudWatch Logs**: ~$5-10/month
- **Secrets Manager**: ~$2/month
- **Total**: ~$60-90/month

### Cost Reduction Tips

1. **Use Spot Instances**: For non-critical workloads
2. **Auto Scaling**: Scale down during low traffic
3. **Reserved Capacity**: For predictable workloads
4. **CloudWatch Alarms**: Monitor and optimize usage

## 🚨 Troubleshooting

### Common Issues

1. **Container Health Check Failing**
   ```bash
   # Check container logs
   aws logs tail /ecs/production-pp-merchantai --region us-east-1
   ```

2. **ECS Tasks Not Starting**
   ```bash
   # Check task definition
   aws ecs describe-task-definition --task-definition production-pp-merchantai --region us-east-1
   ```

3. **Load Balancer Health Check Failing**
   ```bash
   # Check target group health
   aws elbv2 describe-target-health --target-group-arn YOUR_TARGET_GROUP_ARN --region us-east-1
   ```

4. **CloudFront Not Working**
   ```bash
   # Check distribution status
   aws cloudfront get-distribution --id YOUR_DISTRIBUTION_ID --region us-east-1
   ```

### Health Check Endpoints

- **Application Health**: `https://your-domain.com/api/health`
- **Load Balancer Health**: Check ALB target group
- **ECS Service Health**: Check ECS service events

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to AWS
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - name: Deploy to AWS
        run: ./aws/deploy.sh production us-east-1
```

## 📞 Support

For issues with:
- **AWS Infrastructure**: Check CloudFormation stack events
- **Application**: Check ECS logs
- **Deployment**: Review deployment script output

## 🗑️ Cleanup

To remove all resources:

```bash
# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name production-pp-merchantai --region us-east-1

# Delete ECR repository
aws ecr delete-repository --repository-name pp-merchantai --force --region us-east-1

# Delete secrets
aws secretsmanager delete-secret --secret-id pp-merchantai/openai-api-key --force-delete-without-recovery --region us-east-1
aws secretsmanager delete-secret --secret-id pp-merchantai/anthropic-api-key --force-delete-without-recovery --region us-east-1
``` 