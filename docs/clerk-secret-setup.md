# Clerk Secret Key Setup

This document describes the one-time setup required to store the Clerk secret key in AWS Secrets Manager for each environment.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Clerk account with secret keys for each environment
- Appropriate IAM permissions to create secrets

## One-Time Secret Creation

Run these commands **once per environment** (not in CI/CD):

### Dev Environment

```bash
aws secretsmanager create-secret \
  --name trip-cortex/dev/clerk-secret-key \
  --description "Clerk secret key for Trip Cortex dev environment" \
  --secret-string "sk_test_YOUR_DEV_KEY_HERE" \
  --region us-east-1
```

### Staging Environment

```bash
aws secretsmanager create-secret \
  --name trip-cortex/staging/clerk-secret-key \
  --description "Clerk secret key for Trip Cortex staging environment" \
  --secret-string "sk_test_YOUR_STAGING_KEY_HERE" \
  --region us-east-1
```

### Prod Environment

```bash
aws secretsmanager create-secret \
  --name trip-cortex/prod/clerk-secret-key \
  --description "Clerk secret key for Trip Cortex prod environment" \
  --secret-string "sk_live_YOUR_PROD_KEY_HERE" \
  --region us-east-1
```

## Updating samconfig.toml

After creating the secrets, update `samconfig.toml` with the actual ARNs:

1. Get the secret ARN:
   ```bash
   aws secretsmanager describe-secret \
     --secret-id trip-cortex/dev/clerk-secret-key \
     --region us-east-1 \
     --query 'ARN' \
     --output text
   ```

2. Replace `ACCOUNT_ID` in `samconfig.toml` with your AWS account ID, or use the full ARN from step 1.

## Local Development

For local development, the Clerk secret key is read from the `.env` file:

```bash
# .env (never commit this file)
CLERK_SECRET_KEY=sk_test_YOUR_LOCAL_KEY_HERE
```

The local environment does **not** use Secrets Manager.

## Secret Rotation

To rotate the Clerk secret key:

```bash
aws secretsmanager update-secret \
  --secret-id trip-cortex/prod/clerk-secret-key \
  --secret-string "sk_live_NEW_KEY_HERE" \
  --region us-east-1
```

Lambda functions will pick up the new value on their next cold start (no redeployment needed).

## Security Notes

- ✅ Secret **values** are never stored in source control
- ✅ Only secret **ARNs** are in `samconfig.toml`
- ✅ `.env` is in `.gitignore`
- ✅ Use `resolve:secretsmanager` dynamic reference in CloudFormation
- ✅ IAM policies scope access to specific secret ARNs
