# GitHub Actions Workflows

## CI Workflow (`ci.yml`)

Runs on every push and pull request to `main` or `develop` branches.

**Jobs:**
- Lint (ruff)
- Type Check (mypy)
- Unit Tests
- Integration Tests (with PostgreSQL + DynamoDB)
- SAM Build Validation

## Deploy Workflow (`deploy.yml`)

Automatically deploys to AWS environments based on branch using **OIDC (OpenID Connect)** for secure, temporary credentials:
- `main` → dev environment
- `staging` → staging environment
- `prod` → production environment

### AWS OIDC Setup (Required)

The deployment workflow uses OIDC instead of long-lived access keys for security best practices.

#### 1. Create OIDC Identity Provider in AWS

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

#### 2. Create IAM Roles for Each Environment

**Dev Role (`GitHubActionsDeployRole-Dev`):**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<AWS_ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:<GITHUB_ORG>/<REPO_NAME>:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

Attach policies for SAM deployment (CloudFormation, S3, Lambda, IAM, etc.)

**Staging Role:** Same trust policy but with `ref:refs/heads/staging`  
**Prod Role:** Same trust policy but with `ref:refs/heads/prod`

#### 3. Configure GitHub Secrets

Add only the IAM Role ARNs (not access keys):

- `AWS_ROLE_ARN_DEV` - e.g., `arn:aws:iam::123456789012:role/GitHubActionsDeployRole-Dev`
- `AWS_ROLE_ARN_STAGING` - e.g., `arn:aws:iam::123456789012:role/GitHubActionsDeployRole-Staging`
- `AWS_ROLE_ARN_PROD` - e.g., `arn:aws:iam::123456789012:role/GitHubActionsDeployRole-Prod`

### Branch Protection Rules

Configure branch protection in GitHub: **Settings → Branches → Add rule**

**`main` branch:**
- Require status check `ci-gate` to pass before merging
- Require 1 reviewer approval
- Dismiss stale pull request approvals when new commits are pushed
- Include administrators

**`staging` branch:**
- Require status check `ci-gate` to pass before merging
- Require 1 reviewer approval
- Dismiss stale pull request approvals when new commits are pushed

**`prod` branch:**
- Require status check `ci-gate` to pass before merging
- Require 2 reviewer approvals
- Dismiss stale pull request approvals when new commits are pushed
- Include administrators (enforce for everyone)

> **Note:** The `ci-gate` job aggregates all 5 CI jobs (lint, type-check, unit-tests, integration-tests, sam-build) into a single status check. This simplifies branch protection config — you only need to track one check name.

### Environment Protection Rules

Configure environment protection rules in GitHub:

**Production (`prod`):**
- Required reviewers: 2+ team members
- Deployment branches: Only `prod` branch
- Wait timer: Optional 5-minute delay

**Staging (`staging`):**
- Required reviewers: 1+ team member
- Deployment branches: Only `staging` branch

**Dev (`dev`):**
- No protection (auto-deploy on merge to `main`)

### Setup Instructions

1. **AWS Setup:**
   - Create OIDC provider in IAM
   - Create IAM roles for dev/staging/prod with trust policies
   - Attach deployment permissions to roles

2. **GitHub Setup:**
   - Go to repository Settings → Secrets and variables → Actions
   - Add the IAM Role ARNs (AWS_ROLE_ARN_DEV, AWS_ROLE_ARN_STAGING, AWS_ROLE_ARN_PROD)
   - Go to Settings → Environments
   - Create environments: `dev`, `staging`, `prod`
   - Configure protection rules for `staging` and `prod`

### Security Benefits of OIDC

✅ No long-lived credentials stored in GitHub  
✅ Temporary credentials with automatic expiration  
✅ Fine-grained access control per branch  
✅ Audit trail via CloudTrail  
✅ Follows AWS Well-Architected Framework security pillar  
✅ Complies with Zero-Trust security model  

### Rollback

To rollback a deployment:

```bash
# Revert the commit locally
git revert <commit-hash>

# Push to trigger re-deployment
git push origin <branch-name>
```

Or manually deploy a previous version:

```bash
git checkout <previous-commit>
sam build
sam deploy --config-env <environment>
```
