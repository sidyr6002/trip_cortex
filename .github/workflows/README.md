# CI Workflow

```
push to master / PR → CI (lint, types, unit tests, integration tests) → CI Gate
```

## CI (`ci.yml`)

Runs on every push to `master` and on PRs.

| Job | Timeout | Depends On |
|-----|---------|------------|
| lint (ruff + uv.lock check) | 5 min | — |
| type-check (mypy) | 10 min | — |
| unit-tests (pytest + coverage) | 10 min | — |
| integration-tests (postgres + dynamodb) | 15 min | lint, type-check, unit-tests |
| ci-gate (aggregator) | 5 min | all above |
