#!/bin/bash
# Cost-saving script: pause/resume expensive AWS resources when not testing.
#
# Usage:
#   ./scripts/teardown.sh pause       # Stop Aurora, scale down ACUs — saves ~$43/month
#   ./scripts/teardown.sh resume      # Restart Aurora, restore ACUs
#   ./scripts/teardown.sh status      # Check current state
#   ./scripts/teardown.sh delete      # Full stack delete (destructive!)

set -euo pipefail

ENV="${2:-dev}"
REGION="us-east-1"
CLUSTER_ID=$(aws rds describe-db-clusters --region "$REGION" \
  --query "DBClusters[?contains(DBClusterIdentifier,'trip-cortex-${ENV}')].DBClusterIdentifier" \
  --output text 2>/dev/null)

if [ -z "$CLUSTER_ID" ]; then
  echo "❌ No Aurora cluster found for trip-cortex-${ENV}"
  exit 1
fi

case "${1:-status}" in
  pause)
    echo "⏸  Pausing trip-cortex-${ENV} resources..."

    # Scale Aurora to MinCapacity 0 (auto-pauses when idle)
    aws rds modify-db-cluster --region "$REGION" \
      --db-cluster-identifier "$CLUSTER_ID" \
      --serverless-v2-scaling-configuration MinCapacity=0,MaxCapacity=2 \
      --apply-immediately --no-cli-pager
    echo "   ✅ Aurora MinCapacity set to 0 (will auto-pause when idle)"

    # Stop the cluster entirely for immediate savings
    STATUS=$(aws rds describe-db-clusters --region "$REGION" \
      --db-cluster-identifier "$CLUSTER_ID" \
      --query "DBClusters[0].Status" --output text)
    if [ "$STATUS" = "available" ]; then
      aws rds stop-db-cluster --region "$REGION" \
        --db-cluster-identifier "$CLUSTER_ID" --no-cli-pager
      echo "   ✅ Aurora cluster stopping (takes ~1 min)"
      echo "   ⚠️  Auto-restarts after 7 days"
    else
      echo "   ⚠️  Cluster status is '$STATUS', skipping stop"
    fi

    echo ""
    echo "💰 Estimated savings: ~\$43/month (Aurora compute)"
    echo "   NAT Gateway still running (~\$33/month) — cannot pause without infra changes"
    ;;

  resume)
    echo "▶️  Resuming trip-cortex-${ENV} resources..."

    STATUS=$(aws rds describe-db-clusters --region "$REGION" \
      --db-cluster-identifier "$CLUSTER_ID" \
      --query "DBClusters[0].Status" --output text)
    if [ "$STATUS" = "stopped" ]; then
      aws rds start-db-cluster --region "$REGION" \
        --db-cluster-identifier "$CLUSTER_ID" --no-cli-pager
      echo "   ✅ Aurora cluster starting (takes ~30-60s)"
    else
      echo "   ℹ️  Cluster status is '$STATUS', no start needed"
    fi

    # Restore MinCapacity to 0.5 for consistent performance
    aws rds modify-db-cluster --region "$REGION" \
      --db-cluster-identifier "$CLUSTER_ID" \
      --serverless-v2-scaling-configuration MinCapacity=0.5,MaxCapacity=2 \
      --apply-immediately --no-cli-pager
    echo "   ✅ Aurora MinCapacity restored to 0.5"

    echo ""
    echo "⏳ Wait ~60s for cluster to be available before running tests"
    ;;

  status)
    STATUS=$(aws rds describe-db-clusters --region "$REGION" \
      --db-cluster-identifier "$CLUSTER_ID" \
      --query "DBClusters[0].{Status:Status,MinACU:ServerlessV2ScalingConfiguration.MinCapacity,MaxACU:ServerlessV2ScalingConfiguration.MaxCapacity}" \
      --output table)
    echo "Aurora cluster: $CLUSTER_ID"
    echo "$STATUS"
    ;;

  delete)
    echo "🗑  Deleting trip-cortex-${ENV} stack (DESTRUCTIVE)..."
    read -p "Are you sure? Type 'yes' to confirm: " CONFIRM
    if [ "$CONFIRM" = "yes" ]; then
      sam delete --stack-name "trip-cortex-${ENV}" --region "$REGION" --no-prompts
      echo "Done. Stack deleted."
    else
      echo "Aborted."
    fi
    ;;

  *)
    echo "Usage: $0 {pause|resume|status|delete} [env]"
    echo "  env defaults to 'dev'"
    exit 1
    ;;
esac
