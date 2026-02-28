"""Aurora PostgreSQL client — connection management and similarity search."""

import json

import boto3
import psycopg
from pgvector.psycopg import register_vector

from core.config import Config
from core.errors import ErrorCode, PolicyRetrievalError, TripCortexError
from core.models.retrieval import PolicyChunkResult

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

    def similarity_search(
        self,
        query_embedding: list[float],
        threshold: float = 0.65,
        top_k: int = 5,
    ) -> list[PolicyChunkResult]:
        conn = self._require_connection()
        try:
            with conn.cursor() as cur:
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
