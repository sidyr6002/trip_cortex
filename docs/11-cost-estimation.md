# Cost Estimation (MVP)

> Related docs: [Architecture Overview](02-architecture-overview.md) · [Infrastructure](06-infrastructure.md)

---

| Service | Usage Assumption (MVP) | Estimated Monthly Cost |
|---|---|---|
| Bedrock Data Automation (BDA) | Initial ingestion + quarterly re-ingestion (~100 pages) | ~$5–15 (per-page pricing) |
| Nova 2 Lite (Bedrock) | 10,000 requests/month, ~2K tokens avg | ~$25–50 |
| Nova Multimodal Embeddings | 10,000 queries + initial ingestion | ~$10–20 |
| Nova Act (AgentCore Runtime) | 5,000 booking workflows/month | Pricing TBD (check current rates) |
| Aurora PostgreSQL Serverless v2 | 0.5–2 ACUs, bursty | ~$50–100 |
| Lambda | ~50,000 invocations/month | ~$5–10 |
| Step Functions | 10,000 state transitions/month | ~$5 |
| DynamoDB | On-demand, < 1M reads/writes | ~$5–10 |
| API Gateway (WebSocket) | 10,000 connections, 100K messages | ~$5–10 |
| S3 + CloudFront | Static hosting + policy storage | ~$5 |
| Total (estimated) | | ~$110–210/month |

Note: Nova Act pricing on AgentCore Runtime should be verified against current AWS pricing pages, as it was recently made generally available.
