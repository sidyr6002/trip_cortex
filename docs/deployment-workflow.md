# Development & Deployment Workflow

## Dev Workflow (per story)

1. **Write code + unit tests locally** — catches logic bugs, schema mismatches, event format issues
2. **`sam local invoke` with test events** — catches import errors, missing env vars, API contract issues
3. **Deploy once** — `./scripts/deploy.sh dev`
4. **Test end-to-end once**
5. **If code-only fix needed** — update Lambda directly (bypasses CloudFormation):
   ```bash
   sam build && aws lambda update-function-code \
     --function-name <function-name> \
     --zip-file fileb://.aws-sam/build/<FunctionLogicalId>/. \
     --region us-east-1
   ```
6. **Teardown when done** — `./scripts/teardown.sh dev`

## Cost Management

- Aurora Serverless v2 (~$1.44/day) and NAT Gateway (~$1.08/day) run 24/7 when deployed
- **Always teardown** when not actively testing on AWS: `./scripts/teardown.sh dev`
- **Redeploy** when needed: `./scripts/deploy.sh dev` (~5 min)
- Stop Aurora only (keeps stack): `aws rds stop-db-cluster --db-cluster-identifier <id> --region us-east-1` (auto-restarts after 7 days)

## What NOT to use

- `sam sync --watch` — unreliable on Linux, often misses file changes
- `sam sync` — slower than `sam deploy` with nested stacks, no benefit
- `sam sync --code` — skips dependencies, causes `No module named` errors

## Epic 3 Deployment Plan

| Story | Description | Local Dev | AWS Deploy |
|-------|-------------|-----------|------------|
| 3.1 | BDA project setup | ✅ Done | ✅ Done |
| 3.2 | S3→Lambda→BDA→SFN→Aurora orchestrator | ✅ Done | ✅ Done |
| 3.3 | Embedding generator (BDA output → Nova Embeddings) | Code + unit tests with mocked Bedrock | Single deploy at end |
| 3.4 | pgvector storage (INSERT chunks with metadata) | Code + test against local Docker PostgreSQL | Single deploy at end |
| 3.5 | HNSW index creation | SQL migration, test against local Docker PostgreSQL | Single deploy to run migration |
| 3.6 | SQS queue between BDA completion and embedding | Code + unit tests with mocked SQS | Single deploy for SQS infra |

**Stories 3.3–3.5** can be developed together without AWS. One deploy at the end to verify.

**Story 3.6** needs one deploy for the SQS resource, but Lambda code is testable locally.

## Lessons Learned (Story 3.2)

Issues caught at runtime that should have been caught locally:
- EventBridge event format differs from native S3 notification format → `sam local invoke` with correct event
- `dataAutomationProfileArn` required by BDA API → check SDK docs before writing service code
- IAM action `bedrock:InvokeDataAutomation` vs `bedrock:InvokeDataAutomationAsync` → verify exact action names in AWS docs
- `metadata` column missing from policies table → test SQL against local DB schema
- `CheckBdaStatusFunction` connecting to Aurora unnecessarily → `sam local invoke` would have caught this
- Circular dependency between WorkflowStack and FunctionsStack → `sam validate --lint` catches this, always run before deploying
