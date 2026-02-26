# Project Structure & Development Setup

> Related docs: [Architecture Overview](02-architecture-overview.md) · [Infrastructure](06-infrastructure.md) · [Testing Strategy](09-testing-strategy.md)
> ADRs: [009 — Python 3.12](02-architecture-overview.md) · [010 — uv](02-architecture-overview.md) · [011 — Monorepo](02-architecture-overview.md) · [012 — Bundle per Function](02-architecture-overview.md) · [013 — Local Dev](02-architecture-overview.md)

---

## 1. Repository Layout

```
trip-cortex/
├── pyproject.toml                  # Root Python project config (uv)
├── uv.lock                         # Lockfile (committed to git)
├── template.yaml                   # AWS SAM template
├── samconfig.toml                  # SAM deployment config (per-environment)
├── docker-compose.yml              # Local dev: PostgreSQL + DynamoDB Local
├── .env.example                    # Environment variable template
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Lint, unit tests, integration tests
│       └── deploy.yml              # SAM build + deploy (dev/staging/prod)
│
├── src/
│   ├── core/                       # Shared package — all business logic lives here
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── interface.py        # AuthProvider ABC, AuthUser Pydantic model
│   │   │   └── clerk_provider.py   # ClerkAuthProvider (only file importing clerk SDK)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── booking.py          # BookingPlan, BookingParameters, PolicyConstraints
│   │   │   ├── flight.py           # FlightOption, FlightSearchResult
│   │   │   └── websocket.py        # WebSocket message schemas (request, progress, options, error)
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── aurora.py           # Aurora PostgreSQL client (pgvector queries)
│   │   │   └── dynamo.py           # DynamoDB client (bookings, connections, audit, circuit breaker)
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── embedding.py        # Nova MME embedding generation
│   │   │   ├── retrieval.py        # pgvector similarity search + confidence assessment
│   │   │   ├── reasoning.py        # Nova 2 Lite invocation + extended thinking escalation
│   │   │   └── validation.py       # Pydantic schema validation + retry logic
│   │   ├── config.py               # Environment-based config (reads env vars, provides typed config)
│   │   └── errors.py               # Custom exceptions, error codes, user-facing error messages
│   │
│   ├── handlers/                   # Thin Lambda entry points — import from core/
│   │   ├── __init__.py
│   │   ├── connect.py              # WebSocket $connect — auth + store connectionId
│   │   ├── disconnect.py           # WebSocket $disconnect — cleanup connectionId
│   │   ├── booking_request.py      # Receives booking request, enforces single-active check, starts Step Functions
│   │   ├── embed_retrieve.py       # Module 1: embed query + pgvector search
│   │   ├── reason_plan.py          # Module 2: Nova 2 Lite reasoning
│   │   ├── validate_plan.py        # Pydantic validation of BookingPlan
│   │   ├── execute_search.py       # Module 3: triggers Nova Act on AgentCore Runtime
│   │   ├── response_sender.py      # Sends WebSocket messages via @connections API
│   │   ├── heartbeat.py            # WebSocket keepalive (EventBridge scheduled)
│   │   └── ingest_policy.py        # S3 trigger: BDA parsing + embedding pipeline
│   │
│   └── nova_act/                   # Nova Act workflow scripts (deployed to AgentCore Runtime via CLI)
│       ├── flight_search.py        # Search + filter + extract flight options
│       └── flight_booking.py       # Complete booking flow after user selection
│
├── statemachine/
│   └── booking-workflow.asl.json   # Step Functions ASL definition
│
├── tests/
│   ├── conftest.py                 # Shared fixtures (DB clients, mock Bedrock, sample data)
│   ├── unit/                       # Fast, no external dependencies
│   │   ├── test_models.py          # Pydantic model validation
│   │   ├── test_auth.py            # AuthProvider interface + ClerkAuthProvider
│   │   ├── test_validation.py      # Schema validation + retry logic
│   │   ├── test_circuit_breaker.py # Circuit breaker state transitions
│   │   └── test_errors.py          # Error code mapping
│   ├── integration/                # Requires Docker Compose (PostgreSQL, DynamoDB Local)
│   │   ├── test_retrieval.py       # pgvector similarity search with real embeddings
│   │   ├── test_dynamo.py          # DynamoDB CRUD operations
│   │   └── test_reasoning.py       # Bedrock API contract tests (mocked responses)
│   └── e2e/                        # Requires deployed AWS environment
│       └── test_canary.py          # Full booking flow against dummy portal
│
├── dummy-portal/                   # Dummy travel portal (separate sub-project)
│   ├── package.json
│   ├── src/
│   │   ├── index.html
│   │   ├── app.js                  # Flight search UI, results, booking flow
│   │   └── data/
│   │       └── flights.json        # Seed data: deterministic flight options
│   └── README.md
│
├── frontend/                       # React SPA (separate sub-project)
│   ├── package.json
│   ├── src/
│   │   ├── auth/                   # AuthClient interface + ClerkAuthClient
│   │   ├── components/             # Custom sign-in/sign-up UI, booking chat
│   │   └── hooks/                  # useWebSocket, useBooking
│   └── README.md
│
├── scripts/
│   ├── setup-local.sh              # One-command local setup (uv sync, docker compose up, DB migrations)
│   ├── seed-db.sh                  # Seed pgvector with sample policy embeddings
│   └── deploy.sh                   # SAM build + deploy wrapper
│
└── docs/                           # Design documentation (this folder)
    ├── 01-prd.md
    ├── ...
    └── 12-project-structure.md
```

---

## 2. Key Design Principles

### Thin Handlers, Thick Core

Every Lambda handler follows the same pattern:

```python
# src/handlers/reason_plan.py
from core.services.reasoning import generate_booking_plan
from core.config import get_config

def handler(event, context):
    config = get_config()
    result = generate_booking_plan(
        user_query=event["query"],
        policy_chunks=event["policy_chunks"],
        config=config
    )
    return result.model_dump()
```

All logic lives in `core/`. Handlers are 10-20 lines — they parse the Lambda event, call a core function, and return the result. This makes core logic testable without Lambda simulation.

### Provider Abstraction Boundaries

Two abstraction layers prevent vendor lock-in:

```
Backend:  AuthProvider (ABC) → ClerkAuthProvider (only clerk import)
Frontend: AuthClient (interface) → ClerkAuthClient (only @clerk/clerk-js import)
```

Swapping auth providers means implementing one new class on each side.

---

## 3. Dependency Configuration

```toml
# pyproject.toml
[project]
name = "trip-cortex"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "boto3>=1.35.0",
    "pydantic>=2.0",
    "clerk-backend-api>=0.1.0",
    "structlog>=24.0",
    "psycopg[binary]>=3.1",
    "pgvector>=0.3",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "moto>=5.0",           # AWS service mocking
    "ruff>=0.5",           # Linting + formatting
    "mypy>=1.10",          # Type checking
]

[tool.ruff]
target-version = "py312"
line-length = 120

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "unit: fast tests with no external dependencies",
    "integration: requires Docker Compose services",
    "e2e: requires deployed AWS environment",
]
```

---

## 4. Local Development Workflow

### One-Time Setup

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone <repo-url> && cd trip-cortex
uv sync                          # Install all dependencies
cp .env.example .env             # Configure local env vars
docker compose up -d             # Start PostgreSQL + DynamoDB Local
python scripts/setup-local.sh    # Run DB migrations + seed data
```

### Docker Compose (Local Data Stores)

```yaml
# docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg15
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: tripcortex
      POSTGRES_USER: tripcortex
      POSTGRES_PASSWORD: localdev
    volumes:
      - pgdata:/var/lib/postgresql/data

  dynamodb:
    image: amazon/dynamodb-local
    ports:
      - "8000:8000"
    command: "-jar DynamoDBLocal.jar -sharedDb"

volumes:
  pgdata:
```

### Daily Development Loop

```bash
uv run pytest tests/unit/                    # Fast unit tests (~seconds)
uv run pytest tests/integration/ -m integration  # Requires Docker Compose (~30s)
uv run ruff check src/                       # Lint
uv run mypy src/                             # Type check
sam build                                    # Build Lambda packages
sam local invoke ReasonAndPlanFunction -e events/reason.json  # Smoke test
```

### Deploying to Dev

```bash
sam build
sam deploy --config-env dev      # Deploys to dev AWS account
```

---

## 5. SAM Build Integration with uv

SAM needs `requirements.txt` per function. Since all handlers share the same dependencies via `core/`, a single export works:

```bash
# Generate requirements.txt from uv lockfile (used by sam build)
uv pip compile pyproject.toml -o requirements.txt
```

SAM's `sam build` picks up `requirements.txt` from the `CodeUri` directory and installs dependencies into the build artifact. Since all functions use `CodeUri: src/`, they share the same dependency set.

---

## 6. CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg15
        env:
          POSTGRES_DB: tripcortex
          POSTGRES_USER: tripcortex
          POSTGRES_PASSWORD: testpass
        ports:
          - 5432:5432
      dynamodb:
        image: amazon/dynamodb-local
        ports:
          - 8000:8000

    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run ruff check src/ tests/
      - run: uv run mypy src/
      - run: uv run pytest tests/unit/ -v
      - run: uv run pytest tests/integration/ -v
      - run: sam build --use-container
```
