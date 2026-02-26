# Observability & Monitoring

> Related docs: [Architecture Overview](02-architecture-overview.md) · [Infrastructure](06-infrastructure.md) · [Error Handling](07-error-handling.md) · [Testing Strategy](09-testing-strategy.md)

---

## 8.1 CloudWatch Dashboard

| Panel | Metric | Alarm Threshold |
|---|---|---|
| Request Volume | Step Functions executions started/min | > 100/min (capacity alert) |
| E2E Latency | Step Functions execution duration (p50, p95, p99) | p95 > 120 seconds |
| Reasoning Latency | Lambda ReasonAndPlan duration | p95 > 30 seconds |
| Nova Act Success Rate | Successful booking completions / total attempts | < 80% over 15 min |
| RAG Retrieval Quality | Average cosine similarity of top-1 result | < 0.70 average over 1 hour |
| Schema Validation Failures | Count of Pydantic validation errors | > 10% of requests |
| Circuit Breaker State | Portal circuit breaker open events | Any OPEN event |
| WebSocket Connections | Active connection count | > 500 (scaling alert) |

---

## 8.2 Structured Logging

All Lambda functions emit structured JSON logs:

```python
import structlog

logger = structlog.get_logger()

logger.info("policy_retrieval_complete",
    booking_id=booking_id,
    query_length=len(user_query),
    chunks_retrieved=len(chunks),
    max_similarity=max_sim,
    confidence_level=confidence,
    latency_ms=elapsed_ms
)
```
