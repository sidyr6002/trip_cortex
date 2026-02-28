# CI/CD Workflows

```
push to master → CI (lint, types, tests, SAM validate) → auto-deploy to dev
                                                          ↓
                              manual dispatch → deploy to staging
                                                          ↓
                              manual dispatch → deploy to prod
```

## CI (`ci.yml`)

Runs on every push to `master` and on PRs.

| Job | Timeout | Depends On |
|-----|---------|------------|
| lint (ruff + uv.lock check) | 5 min | — |
| type-check (mypy) | 10 min | — |
| unit-tests (pytest + coverage) | 10 min | — |
| integration-tests (postgres + dynamodb) | 15 min | lint, type-check, unit-tests |
| sam-validate (cfn-lint + sam build) | 15 min | lint, type-check, unit-tests |
| ci-gate (aggregator) | 5 min | all above |

## Deploy (`deploy.yml`)

| Environment | Trigger | Changeset |
|-------------|---------|-----------|
| dev | auto (CI pass on master) | auto-confirm |
| staging | manual workflow dispatch | auto-confirm |
| prod | manual workflow dispatch | fail-on-empty |

All environments use OIDC for AWS credentials and per-environment concurrency groups (no parallel deploys).

To promote: **Actions → Deploy → Run workflow → select environment**.
