# GitHub Actions Deploy Role Setup

One-time setup to enable CI/CD deployment from GitHub Actions to AWS.

## Two Layers of IAM

- **Deploy role** (`infra/bootstrap.yaml`) — What GitHub Actions can do during deployment (create stacks, upload Lambda code, manage resources). Used by the CI/CD pipeline.
- **Lambda execution roles** (`infra/functions.yaml`) — What each Lambda function can do at runtime (read DynamoDB, invoke Bedrock, manage WebSocket connections). Managed by SAM/CloudFormation.

## Setup Steps

### 1. Deploy the Bootstrap Stack

```bash
aws cloudformation deploy \
  --template-file infra/bootstrap.yaml \
  --stack-name trip-cortex-bootstrap \
  --capabilities CAPABILITY_NAMED_IAM
```

This creates the GitHub OIDC provider and the deploy role in one shot.

### 2. Create the Clerk Secret (if not already done)

```bash
aws secretsmanager create-secret \
  --name trip-cortex/dev/clerk-secret-key \
  --secret-string "sk_test_YOUR_CLERK_KEY" \
  --region us-east-1
```

### 3. Set GitHub Secrets

```bash
ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name trip-cortex-bootstrap \
  --query 'Stacks[0].Outputs[?OutputKey==`DeployRoleArn`].OutputValue' \
  --output text)

CLERK_ARN=$(aws secretsmanager describe-secret \
  --secret-id trip-cortex/dev/clerk-secret-key \
  --query ARN --output text)

gh secret set AWS_ROLE_ARN_DEV --body "$ROLE_ARN"
gh secret set DEV_CLERK_SECRET_ARN --body "$CLERK_ARN"
```

Repeat for staging/prod when those environments are ready.

## Updating the Deploy Policy

If a deploy fails with `AccessDenied`, the role is missing permissions for a new AWS service. Edit `infra/bootstrap.yaml`, then re-deploy:

```bash
aws cloudformation deploy \
  --template-file infra/bootstrap.yaml \
  --stack-name trip-cortex-bootstrap \
  --capabilities CAPABILITY_NAMED_IAM
```

CloudFormation handles the diff — only changed resources are updated.
