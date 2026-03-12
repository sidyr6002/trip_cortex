#!/usr/bin/env bash
# Local deploy script — reads ARNs from .env.deploy (gitignored)
# Usage: ./scripts/deploy.sh [dev|staging|prod]

set -euo pipefail

ENV="${1:-dev}"

if [ ! -f .env.deploy ]; then
  echo "Error: .env.deploy not found. Copy from .env.deploy.example and fill in ARNs."
  exit 1
fi

source .env.deploy

case "$ENV" in
  dev)
    CLERK_ARN="$DEV_CLERK_SECRET_ARN"
    ;;
  staging)
    CLERK_ARN="$STAGING_CLERK_SECRET_ARN"
    ;;
  prod)
    CLERK_ARN="$PROD_CLERK_SECRET_ARN"
    ;;
  *)
    echo "Error: Unknown environment '$ENV'. Use dev, staging, or prod."
    exit 1
    ;;
esac

sam build
sam deploy --config-env "$ENV" \
  --parameter-overrides "Environment=$ENV ClerkSecretKeyArn=$CLERK_ARN" \
  --no-confirm-changeset
