#!/usr/bin/env bash
# Deploy Nova Act workflows to AgentCore Runtime.
# Usage: bash src/nova_act/deploy.sh  (from project root)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REGION="${AWS_REGION:-us-east-1}"
ACT="$PROJECT_ROOT/.venv/bin/act"
STAGE_DIR="$PROJECT_ROOT/.acr-stage"

# ACR requires arm64 images
export DOCKER_DEFAULT_PLATFORM=linux/arm64

# Prerequisites
aws sts get-caller-identity --region "$REGION" > /dev/null
docker ps > /dev/null 2>&1 || { echo "ERROR: Docker is not running"; exit 1; }

# Build staging directory with only what ACR needs
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"
cp "$SCRIPT_DIR"/*.py "$STAGE_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$STAGE_DIR/"
cp -r "$PROJECT_ROOT/src/core" "$STAGE_DIR/core"
find "$STAGE_DIR" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

cleanup() { rm -rf "$STAGE_DIR"; }
trap cleanup EXIT

deploy_workflow() {
  local name="$1"
  local entry="$2"
  echo "==> Deploying $name..."
  "$ACT" workflow deploy \
    --name "$name" \
    --source-dir "$STAGE_DIR" \
    --entry-point "$entry" \
    --region "$REGION" \
    --overwrite-build-dir
  echo "  ✅ $name deployed"
}

deploy_workflow "trip-cortex-flight-search" "flight_search.py"
deploy_workflow "trip-cortex-flight-booking" "flight_booking.py"

echo ""
echo "Done. Verify with:"
echo "  $ACT workflow show --name trip-cortex-flight-search"
echo "  $ACT workflow show --name trip-cortex-flight-booking"
