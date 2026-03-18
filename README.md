# Trip Cortex

AI-powered corporate travel booking system with automated policy enforcement using Amazon Bedrock and Nova Act.

![Trip Cortex Chat](Images/Screenshot%20from%202026-03-17%2004-51-33.png)
![Trip Cortex Booking](Images/Screenshot%20from%202026-03-17%2004-51-52.png)

## Overview

Trip Cortex is an intelligent travel booking assistant that combines natural language understanding, policy retrieval, and browser automation to streamline corporate travel bookings while ensuring compliance with company travel policies.

- Natural language booking requests via WebSocket chat interface
- Automated travel policy enforcement using RAG (Retrieval-Augmented Generation)
- Browser automation for flight search and booking via Nova Act
- Human-in-the-loop confirmation for flight selection
- Real-time progress updates and audit logging

### Architecture

Serverless event-driven system built on AWS:

| Layer | Services |
|---|---|
| Orchestration | AWS Step Functions, Lambda (Python 3.12, arm64) |
| Knowledge Retrieval | Bedrock Data Automation (PDF parsing), Nova Multimodal Embeddings, Aurora PostgreSQL (pgvector) |
| Reasoning | Nova 2 Lite with Extended Thinking (Converse API) |
| Execution | Nova Act on AgentCore Runtime (browser automation) |
| Data | DynamoDB (bookings, connections, audit logs), S3 (policies, artifacts) |
| Auth | Clerk (JWT via WebSocket authorizer) |
| Frontend | React SPA (Vite + TanStack Router + Tailwind CSS) |
| Dummy Portal | TanStack Start app (the travel site Nova Act automates against) |

The system has three core modules orchestrated by Step Functions:

1. **Module 1 — Policy Knowledge Base**: Ingests travel policy PDFs via BDA, generates embeddings with Nova Multimodal Embeddings (1024-dim), stores/retrieves via pgvector similarity search.
2. **Module 2 — Rules Engine**: Uses Nova 2 Lite with Extended Thinking to reason over policy constraints and produce a structured booking plan.
3. **Module 3 — Booking Agent**: Executes flight search and booking via Nova Act browser automation against the dummy travel portal.

📖 See [docs/](docs/) for detailed architecture, module designs, and ADRs.

---

## Prerequisites

- **Python 3.12+**
- **uv** — Fast Python package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **Node.js 20+** and **pnpm** — For frontend and dummy-portal
- **Docker & Docker Compose** — For local PostgreSQL (pgvector) and DynamoDB Local
- **AWS CLI** — Configured with credentials ([install](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))
- **AWS SAM CLI** — For infrastructure deployment ([install](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html))
- **Clerk account** — For authentication ([clerk.com](https://clerk.com))

### AWS Services You'll Need

Make sure your AWS account has access to:
- Amazon Bedrock (Nova 2 Lite, Nova Multimodal Embeddings, Bedrock Data Automation)
- Amazon Bedrock AgentCore (for Nova Act runtime)
- Aurora Serverless v2 (PostgreSQL)
- DynamoDB
- S3
- Step Functions
- Lambda
- API Gateway (WebSocket)
- Secrets Manager
- CloudWatch

---

## Quick Start

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd trip_cortex

# Backend (Python)
uv sync

# Frontend
cd frontend && pnpm install && cd ..

# Dummy Portal (the travel site Nova Act books against)
cd dummy-portal && pnpm install && cd ..
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

Key variables to set in `.env`:

| Variable | Description |
|---|---|
| `AWS_REGION` | Your AWS region (default: `us-east-1`) |
| `AWS_PROFILE` | AWS CLI profile with Bedrock access |
| `CLERK_SECRET_KEY` | Clerk secret key (for local dev) |
| `CLERK_PUBLISHABLE_KEY` | Clerk publishable key |
| `DUMMY_PORTAL_URL` | URL where you host the dummy portal |

For the frontend:
```bash
cp frontend/.env.example frontend/.env
# Set VITE_CLERK_PUBLISHABLE_KEY and VITE_WS_URL
```

### 3. Start Local Services

```bash
docker compose up -d       # Start PostgreSQL (pgvector) + DynamoDB Local
docker compose ps          # Verify healthy
```

### 4. Set Up Databases

```bash
# Run PostgreSQL migrations (creates pgvector extension, policy tables, etc.)
uv run alembic upgrade head

# Create DynamoDB tables (Bookings, Connections, AuditLog)
uv run python scripts/create_local_tables.py
```

Or use the all-in-one setup script:
```bash
./scripts/setup-local.sh
```

### 5. Set Up the Dummy Portal

The dummy portal is a TanStack Start app that simulates a travel booking website. Nova Act automates against this portal. You need to host it yourself.

```bash
cd dummy-portal
pnpm dev          # Local dev on port 3000
```

For production, the portal is designed to deploy to Cloudflare Workers:
```bash
cd dummy-portal
pnpm build && wrangler deploy
```

Update `DUMMY_PORTAL_URL` in your `.env` to point to wherever you host it.

### 6. Run Tests

```bash
# Unit tests (fast, no external dependencies)
uv run pytest tests/unit/ -v

# Integration tests (requires Docker services running)
uv run pytest tests/integration/ -v -m integration

# All tests
uv run pytest tests/ -v

# With coverage
uv run pytest --cov=src --cov-report=html
```

### 7. Lint and Type Check

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run mypy src/
```

---

## Deployment

### 1. Set Up Secrets

Create the Clerk secret in AWS Secrets Manager:

```bash
aws secretsmanager create-secret \
  --name trip-cortex/dev/clerk-secret-key \
  --description "Clerk secret key for Trip Cortex dev environment" \
  --secret-string "<your-clerk-secret-key>" \
  --region us-east-1
```

Create portal credentials (email/password for the dummy portal, used by Nova Act):

```bash
aws secretsmanager create-secret \
  --name trip-cortex/dev/portal-credentials \
  --description "Dummy portal credentials for Nova Act" \
  --secret-string '{"email":"<email>","password":"<password>"}' \
  --region us-east-1
```

See [docs/clerk-secret-setup.md](docs/clerk-secret-setup.md) for details.

### 2. Deploy Nova Act Workflows to AgentCore

Nova Act scripts live in `src/booking_agent/` and deploy to AgentCore Runtime (not Lambda):

```bash
cd src/booking_agent
./deploy.sh
```

This registers the flight search and booking workflows. Note the agent ARNs from the output.

### 3. Configure Deploy Environment

```bash
cp .env.deploy.example .env.deploy
# Fill in the ARNs from steps 1-2
```

### 4. Deploy Infrastructure

```bash
# Build
sam build

# Deploy (uses scripts/deploy.sh which reads .env.deploy)
./scripts/deploy.sh dev

# Or manually:
sam deploy --config-env dev \
  --parameter-overrides "Environment=dev ClerkSecretKeyArn=<arn> NovaActBookingAgentArn=<arn> PortalCredentialsSecretArn=<arn> DummyPortalUrl=<url>"
```

Environments are configured in `samconfig.toml`: `dev`, `staging`, `prod`.

### 5. Deploy Frontend

The frontend is a React SPA. After deploying the backend, update `frontend/.env` with the WebSocket URL from the API Gateway output, then build and host it (S3 + CloudFront, Vercel, Netlify, etc.):

```bash
cd frontend
pnpm build    # Output in dist/
```

### Cost Management

Use the teardown script to pause expensive resources when not testing:

```bash
./scripts/teardown.sh pause       # Stop Aurora — saves ~$43/month
./scripts/teardown.sh resume      # Restart Aurora
./scripts/teardown.sh status      # Check current state
./scripts/teardown.sh delete      # Full stack delete (destructive!)
```

---

## Project Structure

```
trip_cortex/
├── src/
│   ├── core/                    # Shared business logic (thick core)
│   │   ├── auth/                # Clerk auth abstraction
│   │   ├── models/              # Pydantic models (booking, ingestion, retrieval, etc.)
│   │   ├── db/                  # Aurora (pgvector) and DynamoDB clients
│   │   ├── services/            # All business logic lives here
│   │   │   ├── reasoning.py     # Nova 2 Lite Converse API integration
│   │   │   ├── embedding.py     # Nova MME embedding generation
│   │   │   ├── policy_retrieval.py  # pgvector similarity search
│   │   │   ├── ingestion.py     # BDA document processing
│   │   │   ├── circuit_breaker.py   # Circuit breaker for Nova Act
│   │   │   └── ...
│   │   ├── config.py            # Environment configuration (Pydantic)
│   │   └── errors.py            # Custom exceptions
│   ├── handlers/                # Lambda entry points (thin — 10-20 lines each)
│   ├── booking_agent/           # Nova Act scripts (deploy to AgentCore, NOT Lambda)
│   └── alembic/                 # Database migrations
├── frontend/                    # React SPA (Vite + TanStack Router + Clerk)
├── dummy-portal/                # FlySmart travel portal (TanStack Start + Cloudflare Workers)
├── statemachine/                # Step Functions ASL definitions
├── infra/                       # CloudFormation nested stacks
│   └── stacks/                  # network.yaml, aurora.yaml, tables.yaml, etc.
├── tests/
│   ├── unit/                    # Fast, no external deps
│   ├── integration/             # Requires Docker services
│   ├── smoke/                   # Nova Act smoke tests
│   └── e2e/                     # Requires deployed AWS environment
├── scripts/                     # Setup, deploy, teardown scripts
├── docs/                        # Architecture and design documentation
├── alembic/                     # Root alembic config (local dev migrations)
├── template.yaml                # SAM template (main)
├── samconfig.toml               # SAM deploy config per environment
├── docker-compose.yml           # Local PostgreSQL + DynamoDB
└── pyproject.toml               # Python dependencies (managed by uv)
```

**Key principle:** Handlers are thin (parse event → call core → return result). All business logic lives in `src/core/`.

---

## Key Documentation

| Doc | Description |
|---|---|
| [PRD](docs/01-prd.md) | Product requirements and user stories |
| [Architecture Overview](docs/02-architecture-overview.md) | System design, execution flow, and ADRs |
| [Module 1: Ingestion Pipeline](docs/03-module-ingestion-pipeline.md) | BDA parsing, embedding generation, pgvector storage |
| [Module 2: Rules Engine](docs/04-module-rules-engine.md) | Nova 2 Lite reasoning with Extended Thinking |
| [Module 3: Booking Agent](docs/05-module-booking-agent.md) | Nova Act integration and AgentCore deployment |
| [Infrastructure](docs/06-infrastructure.md) | SAM template, VPC, Aurora, DynamoDB |
| [Error Handling](docs/07-error-handling.md) | Retry strategies, circuit breaker, graceful degradation |
| [Security](docs/08-security.md) | Auth, encryption, IAM least privilege |
| [Testing Strategy](docs/09-testing-strategy.md) | Unit, integration, E2E, RAG evaluation |
| [Observability](docs/10-observability.md) | Structured logging, metrics, alarms |
| [Database Design](docs/13-database-design.md) | Aurora schema, DynamoDB table designs |
| [Project Structure](docs/12-project-structure.md) | Repository layout and conventions |

---

## CI/CD

GitHub Actions workflows in `.github/workflows/`:

- **CI** (`ci.yml`) — Lint, type check, unit tests, integration tests, SAM build validation. Runs on every push/PR.
- **Deploy** (`deploy.yml`) — Automated deployment to dev/staging/prod based on branch.

See [docs/github-actions-deploy-role.md](docs/github-actions-deploy-role.md) for IAM role setup.

---

## Contributing

1. Create a feature branch from `main`
2. Follow the thin handlers / thick core pattern
3. Add tests (unit required, integration recommended)
4. Lint and type check: `uv run ruff check src/ && uv run mypy src/`
5. Ensure all tests pass: `uv run pytest tests/`
6. Submit a pull request

---

## License

MIT
