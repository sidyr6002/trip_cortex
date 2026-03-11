#!/bin/bash
set -e
ENV=${1:-dev}
echo "Tearing down trip-cortex-$ENV..."
sam delete --stack-name "trip-cortex-$ENV" --region us-east-1 --no-prompts
echo "Done. Stack deleted."
