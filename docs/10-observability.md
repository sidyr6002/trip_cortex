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
| RAG Retrieval Quality | Average cosine similarity of top-1 result | < 0.70 average over 1 hour (see §8.3) |
| Schema Validation Failures | Count of Pydantic validation errors | > 10% of requests |
| Circuit Breaker State | Portal circuit breaker open events | Any OPEN event |
| WebSocket Connections | Active connection count | > 500 (scaling alert) |

---

## 8.3 Alarm Configuration: Avoiding False Positives on Low Traffic

CloudWatch alarms evaluate metrics over rolling windows. For metrics derived from per-request log data (like RAG Retrieval Quality), low traffic volumes can cause a single outlier to trigger a false alarm — e.g., one request with `max_similarity = 0.60` would make the 1-hour average 0.60 and fire the alarm.

To prevent this, configure alarms with composite evaluation:

| Setting | Value | Reasoning |
|---|---|---|
| Evaluation period | 5 minutes | Granular enough to detect sustained degradation |
| Number of evaluation periods | 12 | Covers the full 1-hour window |
| Datapoints to alarm | 3 out of 12 | Requires degradation across multiple periods before firing; a single bad request won't trigger |
| Treat missing data | `ignore` | Periods with no requests are skipped rather than counting for or against the threshold |

This means the alarm only fires when at least 3 separate 5-minute windows within the hour show an average similarity below 0.70 — filtering out one-off outliers while still catching genuine retrieval quality regressions.

These settings apply to any low-throughput metric alarm (RAG Retrieval Quality, Schema Validation Failures). High-throughput alarms like Request Volume and E2E Latency are less susceptible to single-outlier noise and can use simpler threshold evaluation.

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
