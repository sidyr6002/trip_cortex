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
    PORTAL_CREDS_ARN="$DEV_PORTAL_CREDENTIALS_ARN"
    BOOKING_AGENT_ARN="$DEV_NOVA_ACT_BOOKING_AGENT_ARN"
    DUMMY_PORTAL_URL="$DEV_DUMMY_PORTAL_URL"
    ;;
  staging)
    CLERK_ARN="$STAGING_CLERK_SECRET_ARN"
    PORTAL_CREDS_ARN="$STAGING_PORTAL_CREDENTIALS_ARN"
    BOOKING_AGENT_ARN="$STAGING_NOVA_ACT_BOOKING_AGENT_ARN"
    DUMMY_PORTAL_URL="$STAGING_DUMMY_PORTAL_URL"
    ;;
  prod)
    CLERK_ARN="$PROD_CLERK_SECRET_ARN"
    PORTAL_CREDS_ARN="$PROD_PORTAL_CREDENTIALS_ARN"
    BOOKING_AGENT_ARN="$PROD_NOVA_ACT_BOOKING_AGENT_ARN"
    DUMMY_PORTAL_URL="$PROD_DUMMY_PORTAL_URL"
    ;;
  *)
    echo "Error: Unknown environment '$ENV'. Use dev, staging, or prod."
    exit 1
    ;;
esac

sam build
sam deploy --config-env "$ENV" \
  --parameter-overrides "Environment=$ENV ClerkSecretKeyArn=$CLERK_ARN NovaActBookingAgentArn=$BOOKING_AGENT_ARN PortalCredentialsSecretArn=$PORTAL_CREDS_ARN DummyPortalUrl=$DUMMY_PORTAL_URL" \
  --no-confirm-changeset
