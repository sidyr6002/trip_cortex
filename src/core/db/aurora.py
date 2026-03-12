"""Aurora PostgreSQL client — connection management and similarity search."""

import json

import boto3
import psycopg
import structlog
from pgvector.psycopg import register_vector

from core.config import Config
from core.errors import ErrorCode, PolicyRetrievalError, TripCortexError
from core.models.retrieval import PolicyChunkResult

logger = structlog.get_logger()

_INSERT_CHUNK_SQL = """
    INSERT INTO policy_chunks
        (policy_id, content_type, content_text, source_page, section_title,
         reading_order, bda_entity_id, bda_entity_subtype, embedding, metadata)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (policy_id, bda_entity_id)
    DO UPDATE SET
        embedding = EXCLUDED.embedding,
        updated_at = NOW()
"""

_SIMILARITY_SEARCH_SQL = """
    WITH query AS (
        SELECT %s::vector AS vec
    )
    SELECT pc.id, pc.content_text, pc.section_title, pc.source_page,
           pc.content_type, pc.bda_entity_subtype,
           1 - (pc.embedding <=> q.vec) AS similarity
    FROM policy_chunks pc, query q
    WHERE 1 - (pc.embedding <=> q.vec) >= %s
    ORDER BY pc.embedding <=> q.vec
    LIMIT %s
"""


class AuroraClient:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._conn: psycopg.Connection | None = None
        self._secret_cache: dict[str, str] | None = None

    def _get_credentials(self) -> dict[str, str]:
        if self._config.aurora_secret_arn:
            if self._secret_cache is None:
                client = boto3.client("secretsmanager", region_name=self._config.aws_region)
                secret = client.get_secret_value(SecretId=self._config.aurora_secret_arn)
                self._secret_cache = json.loads(secret["SecretString"])
            return self._secret_cache
        return {
            "host": self._config.aurora_host,
            "port": str(self._config.aurora_port),
            "dbname": self._config.aurora_database,
            "user": self._config.aurora_user,
            "password": self._config.aurora_password,
        }

    def connect(self) -> None:
        creds = self._get_credentials()
        self._conn = psycopg.connect(
            host=creds.get("host", self._config.aurora_host),
            port=int(creds.get("port", self._config.aurora_port)),
            dbname=creds.get("dbname", self._config.aurora_database),
            user=creds.get("username", creds.get("user", self._config.aurora_user)),
            password=creds.get("password", self._config.aurora_password),
        )
        register_vector(self._conn)
        self.verify_hnsw_index()

    def verify_hnsw_index(self) -> bool:
        """Verify HNSW index exists with expected configuration. Logs error but does not raise."""
        conn = self._require_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT indexdef FROM pg_indexes "
                "WHERE tablename = 'policy_chunks' AND indexname = 'idx_policy_chunks_embedding'"
            )
            row = cur.fetchone()
        if row is None:
            logger.error("hnsw_index_missing", index="idx_policy_chunks_embedding")
            return False
        indexdef = row[0].lower()
        valid = "hnsw" in indexdef and "vector_cosine_ops" in indexdef
        if valid:
            logger.info("hnsw_index_verified", index="idx_policy_chunks_embedding")
        else:
            logger.error("hnsw_index_misconfigured", indexdef=indexdef)
        return valid

    def disconnect(self) -> None:
        if self._conn and not self._conn.closed:
            self._conn.close()
        self._conn = None

    def _require_connection(self) -> psycopg.Connection:
        """Return the active connection or raise if not connected."""
        if self._conn is None or self._conn.closed:
            raise TripCortexError("AuroraClient is not connected. Call connect() first.")
        return self._conn

    def health_check(self) -> bool:
        try:
            conn = self._require_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception:
            return False

    def insert_chunks(self, chunks: list[dict]) -> int:
        """Batch upsert policy chunks. Returns count inserted."""
        if not chunks:
            return 0
        conn = self._require_connection()
        rows = [
            (
                c["policy_id"], c["content_type"], c["content_text"], c["source_page"],
                c["section_title"], c["reading_order"], c["bda_entity_id"],
                c["bda_entity_subtype"], c["embedding"], c["metadata"],
            )
            for c in chunks
        ]
        try:
            with conn.cursor() as cur:
                cur.executemany(_INSERT_CHUNK_SQL, rows)
            conn.commit()
            return len(chunks)
        except Exception as e:
            conn.rollback()
            logger.error("insert_chunks_failed", exc_info=True)
            raise PolicyRetrievalError(
                f"Failed to insert chunks: {e}", code=ErrorCode.RETRIEVAL_FAILED
            ) from e

    def update_policy_status(self, policy_id: str, status: str, total_chunks: int) -> None:
        """Update policy status and chunk count after embedding."""
        conn = self._require_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE policies SET status = %s, total_chunks = %s WHERE id = %s",
                    (status, total_chunks, policy_id),
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise PolicyRetrievalError(
                f"Failed to update policy status: {e}", code=ErrorCode.RETRIEVAL_FAILED
            ) from e

    def similarity_search(
        self,
        query_embedding: list[float],
        threshold: float = 0.65,
        top_k: int = 5,
        ef_search: int = 40,
    ) -> list[PolicyChunkResult]:
        conn = self._require_connection()
        try:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(f"SET LOCAL hnsw.ef_search = {int(ef_search)}")
                    cur.execute(_SIMILARITY_SEARCH_SQL, (query_embedding, threshold, top_k))
                    rows = cur.fetchall()
        except Exception as e:
            raise PolicyRetrievalError(
                f"Similarity search failed: {e}",
                code=ErrorCode.RETRIEVAL_FAILED,
            ) from e

        return [
            PolicyChunkResult(
                id=str(row[0]),
                content_text=row[1],
                section_title=row[2],
                source_page=row[3],
                content_type=row[4],
                bda_entity_subtype=row[5],
                similarity=float(row[6]),
            )
            for row in rows
        ]

    def __enter__(self) -> "AuroraClient":
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.disconnect()
