# Trip Cortex

AI-powered corporate travel booking system with automated policy enforcement using Amazon Bedrock and Nova Act.

## Overview

Trip Cortex is an intelligent travel booking assistant that combines natural language understanding, policy retrieval, and browser automation to streamline corporate travel bookings while ensuring compliance with company travel policies.

**Key Features:**
- Natural language booking requests via WebSocket chat interface
- Automated travel policy enforcement using RAG (Retrieval-Augmented Generation)
- Browser automation for flight search and booking via Nova Act
- Human-in-the-loop confirmation for flight selection
- Real-time progress updates and audit logging

**Architecture:** Serverless event-driven system using AWS Lambda, Step Functions, Aurora PostgreSQL (pgvector), DynamoDB, and Amazon Bedrock (Nova 2 Lite, Nova Multimodal Embeddings, Bedrock Data Automation).

📖 **Documentation:** See [docs/](docs/) for detailed architecture, module designs, and ADRs.  
📋 **Implementation Plan:** See [plans/epics_blueprint.md](plans/epics_blueprint.md) for the full development roadmap.

---

## Prerequisites

- **Python 3.12+**
- **uv** - Fast Python package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **Docker & Docker Compose** - For local PostgreSQL and DynamoDB
- **AWS CLI** - Configured with credentials for deployment
- **AWS SAM CLI** - For infrastructure deployment ([install](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html))

---

## Quick Start

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd trip_cortex
uv sync                    # Install all dependencies (production + dev)
```

### 2. Configure Environment

```bash
cp .env.example .env       # Copy environment template
# Edit .env with your local configuration
```

### 3. Start Local Services

```bash
docker compose up -d       # Start PostgreSQL + DynamoDB Local
```

Verify services are running:
```bash
docker compose ps          # Should show postgres and dynamodb as healthy
```

### 4. Run Tests

```bash
# Unit tests (fast, no external dependencies)
uv run pytest tests/unit/ -v

# Integration tests (requires Docker services)
uv run pytest tests/integration/ -v -m integration

# All tests
uv run pytest tests/ -v
```

### 5. Lint and Type Check

```bash
uv run ruff check src/ tests/     # Lint
uv run ruff format src/ tests/    # Format
uv run mypy src/                  # Type check
```

---

## Development Workflow

### Project Structure

```
trip-cortex/
├── src/
│   ├── core/              # Shared business logic (thick core)
│   │   ├── auth/          # Authentication abstraction
│   │   ├── models/        # Pydantic models
│   │   ├── db/            # Database clients (Aurora, DynamoDB)
│   │   ├── services/      # Business services (embedding, retrieval, reasoning)
│   │   ├── config.py      # Environment configuration
│   │   └── errors.py      # Custom exceptions
│   ├── handlers/          # Lambda entry points (thin handlers)
│   └── nova_act/          # Nova Act workflow scripts
├── tests/
│   ├── unit/              # Fast unit tests
│   ├── integration/       # Tests requiring Docker services
│   └── e2e/               # End-to-end canary tests
├── statemachine/          # Step Functions ASL definitions
├── docs/                  # Architecture and design documentation
```

**Key Principle:** Handlers are thin (10-20 lines) — all logic lives in `core/`.

### Adding Dependencies

```bash
# Production dependency
uv add <package-name>

# Development dependency
uv add --dev <package-name>

# After adding dependencies, regenerate requirements.txt for SAM
uv pip compile pyproject.toml -o requirements.txt
```

### Local Development with SAM

```bash
# Build Lambda packages
sam build

# Invoke a function locally
sam local invoke ReasonAndPlanFunction -e events/reason.json

# Start local API Gateway
sam local start-api
```

---

## Deployment

### Prerequisites

Before deploying to AWS, you must create the Clerk secret in AWS Secrets Manager for each environment:

```bash
# Create secret for dev environment
aws secretsmanager create-secret \
  --name trip-cortex/dev/clerk-secret-key \
  --description "Clerk secret key for Trip Cortex dev environment" \
  --secret-string "sk_test_YOUR_DEV_KEY_HERE" \
  --region us-east-1

# Get the ARN and update samconfig.toml
aws secretsmanager describe-secret \
  --secret-id trip-cortex/dev/clerk-secret-key \
  --region us-east-1 \
  --query 'ARN' \
  --output text
```

Repeat for `staging` and `prod` environments. See [docs/clerk-secret-setup.md](docs/clerk-secret-setup.md) for detailed instructions.

### Deploy to AWS

```bash
# Build
sam build

# Deploy to dev environment
sam deploy --config-env dev

# Deploy to staging
sam deploy --config-env staging

# Deploy to production (requires approval)
sam deploy --config-env prod
```

### Environment Configuration

Environments are configured in `samconfig.toml`:
- **dev** - Development environment for testing
- **staging** - Pre-production environment
- **prod** - Production environment

---

## Architecture

Trip Cortex consists of three core modules orchestrated by AWS Step Functions:

1. **Module 1: Policy Knowledge Base** - Ingests travel policies using Bedrock Data Automation, generates embeddings with Nova Multimodal Embeddings, and retrieves relevant policy chunks via pgvector similarity search.

2. **Module 2: Rules Engine** - Uses Nova 2 Lite with Extended Thinking to reason over policy constraints and generate a structured booking plan.

3. **Module 3: Booking Agent** - Executes flight search and booking via Nova Act browser automation against a dummy travel portal.

**Communication:** WebSocket API for real-time client updates with human-in-the-loop confirmation.

See [docs/02-architecture-overview.md](docs/02-architecture-overview.md) for detailed architecture and ADRs.

---

## Key Documentation

- [PRD](docs/01-prd.md) - Product requirements and user stories
- [Architecture Overview](docs/02-architecture-overview.md) - System design and ADRs
- [Module 1: Ingestion Pipeline](docs/03-module-ingestion-pipeline.md) - Policy ingestion and retrieval
- [Module 2: Rules Engine](docs/04-module-rules-engine.md) - Reasoning and planning
- [Module 3: Booking Agent](docs/05-module-booking-agent.md) - Nova Act integration
- [Infrastructure](docs/06-infrastructure.md) - AWS resources and SAM template
- [Error Handling](docs/07-error-handling.md) - Retry strategies and graceful degradation
- [Security](docs/08-security.md) - Authentication, encryption, IAM policies
- [Testing Strategy](docs/09-testing-strategy.md) - Unit, integration, E2E, RAG evaluation
- [Observability](docs/10-observability.md) - Logging, metrics, alarms
- [Project Structure](docs/12-project-structure.md) - Repository layout and conventions

---

## Testing

### Test Categories

- **Unit Tests** (`tests/unit/`) - Fast, no external dependencies. Run on every commit.
- **Integration Tests** (`tests/integration/`) - Require Docker Compose services (PostgreSQL, DynamoDB Local).
- **E2E Tests** (`tests/e2e/`) - Require deployed AWS environment. Run as canary tests.

### Running Specific Test Types

```bash
# Only unit tests
uv run pytest tests/unit/ -v

# Only integration tests
uv run pytest -m integration -v

# Only E2E tests (requires AWS deployment)
uv run pytest -m e2e -v

# With coverage
uv run pytest --cov=src --cov-report=html
```

---

## CI/CD

GitHub Actions workflows automatically run on every push and pull request:

- **CI Workflow** (`.github/workflows/ci.yml`) - Lint, type check, unit tests, integration tests, SAM build validation
- **Deploy Workflow** (`.github/workflows/deploy.yml`) - Automated deployment to dev/staging/prod based on branch

---

## Contributing

1. Create a feature branch from `main`
2. Make changes following the thin handlers / thick core pattern
3. Add tests (unit tests required, integration tests recommended)
4. Run linting and type checks: `uv run ruff check src/ && uv run mypy src/`
5. Ensure all tests pass: `uv run pytest tests/`
6. Submit a pull request

---

## License

[Add license information]

---

## Support

For questions or issues, see [docs/](docs/) or contact the development team.
