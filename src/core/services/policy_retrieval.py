"""Policy retrieval service — embed query, similarity search, confidence assessment, context assembly."""

import time

import structlog

from core.config import Config
from core.db.aurora import AuroraClient
from core.models.retrieval import (
    ConfidenceAssessment,
    ConfidenceLevel,
    PolicyChunkResult,
    RetrievalResult,
)
from core.services.query_embedding import QueryEmbeddingService

logger = structlog.get_logger()


class PolicyRetrievalService:
    def __init__(
        self,
        query_embedding_service: QueryEmbeddingService,
        aurora_client: AuroraClient,
        config: Config,
    ) -> None:
        self._query_embedding_service = query_embedding_service
        self._aurora_client = aurora_client
        self._config = config

    def retrieve(self, query_text: str, content_type: str | None = None) -> RetrievalResult:
        start = time.monotonic()
        embedding = self._query_embedding_service.embed_query(query_text)
        chunks = self._aurora_client.similarity_search(
            query_embedding=embedding,
            threshold=self._config.similarity_threshold,
            top_k=self._config.retrieval_top_k,
            ef_search=self._config.hnsw_ef_search,
            content_type=content_type,
        )
        confidence = self._assess_confidence(chunks)
        context_text = self._assemble_context(chunks)
        latency_ms = round((time.monotonic() - start) * 1000, 1)

        logger.info(
            "policy_retrieved",
            results_count=len(chunks),
            confidence_level=confidence.level.value,
            max_similarity=confidence.max_similarity,
            action=confidence.action,
            latency_ms=latency_ms,
        )
        return RetrievalResult(
            chunks=chunks,
            confidence=confidence,
            context_text=context_text,
            total_chunks=len(chunks),
            latency_ms=latency_ms,
        )

    def _assess_confidence(self, chunks: list[PolicyChunkResult]) -> ConfidenceAssessment:
        if not chunks:
            return ConfidenceAssessment(level=ConfidenceLevel.NONE, max_similarity=0.0, action="apply_strict_defaults")
        max_sim = max(c.similarity for c in chunks)
        if max_sim > self._config.high_confidence_threshold:
            return ConfidenceAssessment(level=ConfidenceLevel.HIGH, max_similarity=max_sim, action="normal")
        return ConfidenceAssessment(level=ConfidenceLevel.LOW, max_similarity=max_sim, action="flag_low_confidence")

    def _assemble_context(self, chunks: list[PolicyChunkResult]) -> str:
        if not chunks:
            return ""
        parts = [
            f"[Section: {c.section_title} | Page: {c.source_page} | Type: {c.content_type}"
            f" | Similarity: {c.similarity:.2f}]\n{c.content_text}"
            for c in chunks
        ]
        return "\n---\n".join(parts)
