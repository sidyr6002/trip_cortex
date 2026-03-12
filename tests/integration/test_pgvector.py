"""Integration tests for PostgreSQL pgvector operations."""

import pytest
from psycopg.types.json import Json


@pytest.mark.integration
def test_pgvector_extension_loaded(pg_connection):
    """Test that pgvector extension is installed."""
    with pg_connection.cursor() as cur:
        cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        result = cur.fetchone()
        assert result is not None
        assert result[0] == "vector"


@pytest.mark.integration
def test_policy_chunks_table_exists(pg_connection):
    """Test that policy_chunks table exists with correct columns."""
    with pg_connection.cursor() as cur:
        # Check table exists
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'policy_chunks'
        """)
        assert cur.fetchone() is not None

        # Check columns
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'policy_chunks'
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()
        column_names = [col[0] for col in columns]

        # Verify key columns exist
        assert "id" in column_names
        assert "policy_id" in column_names
        assert "content_type" in column_names
        assert "content_text" in column_names
        assert "embedding" in column_names
        assert "metadata" in column_names
        assert "created_at" in column_names


@pytest.mark.integration
def test_insert_and_retrieve_chunk(pg_connection, pg_policy_id):
    """Test inserting and retrieving a policy chunk with vector."""
    vector = [0.001] * 1024
    vector_str = "[" + ",".join(str(v) for v in vector) + "]"

    with pg_connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO policy_chunks
            (policy_id, content_type, content_text, embedding, metadata)
            VALUES (%s, %s, %s, %s::vector, %s)
            RETURNING id
        """,
            (
                pg_policy_id,
                "text",
                "Employees must book flights at least 7 days in advance.",
                vector_str,
                Json({"source": "test"}),
            ),
        )
        chunk_id = cur.fetchone()[0]
        pg_connection.commit()

        cur.execute(
            """
            SELECT id, policy_id, content_type, content_text, metadata
            FROM policy_chunks WHERE id = %s
        """,
            (chunk_id,),
        )
        result = cur.fetchone()

        assert result is not None
        assert result[0] == chunk_id
        assert result[1] == pg_policy_id
        assert result[2] == "text"
        assert "7 days in advance" in result[3]
        assert result[4]["source"] == "test"


@pytest.mark.integration
def test_cosine_similarity_search(pg_connection, pg_policy_id):
    """Test vector similarity search with cosine distance."""
    vector1 = [1.0] * 512 + [0.0] * 512
    vector2 = [0.0] * 512 + [1.0] * 512
    vector3 = [0.9] * 512 + [0.1] * 512

    v1_str = "[" + ",".join(str(v) for v in vector1) + "]"
    v2_str = "[" + ",".join(str(v) for v in vector2) + "]"
    v3_str = "[" + ",".join(str(v) for v in vector3) + "]"

    with pg_connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO policy_chunks (policy_id, content_type, content_text, embedding)
            VALUES
                (%s, 'text', 'Chunk 1', %s::vector),
                (%s, 'text', 'Chunk 2', %s::vector),
                (%s, 'text', 'Chunk 3', %s::vector)
        """,
            (
                pg_policy_id,
                v1_str,
                pg_policy_id,
                v2_str,
                pg_policy_id,
                v3_str,
            ),
        )
        pg_connection.commit()

        query_str = "[" + ",".join(str(v) for v in vector1) + "]"
        cur.execute(
            """
            SELECT id, content_text, embedding <=> %s::vector AS distance
            FROM policy_chunks WHERE policy_id = %s
            ORDER BY embedding <=> %s::vector LIMIT 3
        """,
            (query_str, pg_policy_id, query_str),
        )
        results = cur.fetchall()

        assert len(results) == 3
        distances = [row[2] for row in results]
        assert distances[0] < distances[2]
        assert distances == sorted(distances)


@pytest.mark.integration
def test_insert_chunk_with_full_metadata(pg_connection, pg_policy_id):
    """All metadata columns round-trip correctly."""
    vector_str = "[" + ",".join(["0.1"] * 1024) + "]"
    with pg_connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO policy_chunks
                (policy_id, content_type, content_text, source_page, section_title,
                 reading_order, bda_entity_id, bda_entity_subtype, embedding, metadata)
            VALUES (%s, 'text', %s, %s, %s, %s, %s, %s, %s::vector, %s)
            RETURNING id
            """,
            (pg_policy_id, "Book 14 days in advance.", 3, "Air Travel Policy",
             5, "bda-entity-001", "PARAGRAPH", vector_str,
             Json({"bounding_box": {"x": 0.1, "y": 0.2}})),
        )
        chunk_id = cur.fetchone()[0]
        pg_connection.commit()

        cur.execute(
            "SELECT section_title, source_page, reading_order, bda_entity_id, bda_entity_subtype, metadata "
            "FROM policy_chunks WHERE id = %s",
            (chunk_id,),
        )
        row = cur.fetchone()

    assert row[0] == "Air Travel Policy"
    assert row[1] == 3
    assert row[2] == 5
    assert row[3] == "bda-entity-001"
    assert row[4] == "PARAGRAPH"
    assert row[5]["bounding_box"]["x"] == 0.1


@pytest.mark.integration
def test_upsert_on_duplicate_bda_entity_id(pg_connection, pg_policy_id):
    """Re-ingesting the same entity updates embedding, no duplicate row."""
    vector_str = "[" + ",".join(["0.1"] * 1024) + "]"
    new_vector_str = "[" + ",".join(["0.9"] * 1024) + "]"
    upsert_sql = """
        INSERT INTO policy_chunks (policy_id, content_type, content_text, embedding, bda_entity_id)
        VALUES (%s, 'text', %s, %s::vector, %s)
        ON CONFLICT (policy_id, bda_entity_id) DO UPDATE SET embedding = EXCLUDED.embedding
    """
    with pg_connection.cursor() as cur:
        cur.execute(upsert_sql, (pg_policy_id, "Original", vector_str, "bda-dup-001"))
        cur.execute(upsert_sql, (pg_policy_id, "Updated", new_vector_str, "bda-dup-001"))
        pg_connection.commit()
        cur.execute(
            "SELECT COUNT(*) FROM policy_chunks WHERE policy_id = %s AND bda_entity_id = 'bda-dup-001'",
            (pg_policy_id,),
        )
        assert cur.fetchone()[0] == 1


@pytest.mark.integration
def test_cascade_delete_removes_chunks(pg_connection):
    """Deleting a policy removes all its chunks."""
    # Create a dedicated policy so teardown doesn't conflict
    with pg_connection.cursor() as cur:
        cur.execute(
            "INSERT INTO policies (source_s3_uri, file_name) VALUES ('s3://test/cascade.pdf', 'cascade.pdf') RETURNING id"
        )
        policy_id = cur.fetchone()[0]
        pg_connection.commit()

    vector_str = "[" + ",".join(["0.5"] * 1024) + "]"
    with pg_connection.cursor() as cur:
        cur.execute(
            "INSERT INTO policy_chunks (policy_id, content_type, content_text, embedding) "
            "VALUES (%s, 'text', 'test', %s::vector)",
            (policy_id, vector_str),
        )
        cur.execute("DELETE FROM policies WHERE id = %s", (policy_id,))
        pg_connection.commit()
        cur.execute("SELECT COUNT(*) FROM policy_chunks WHERE policy_id = %s", (policy_id,))
        assert cur.fetchone()[0] == 0


@pytest.mark.integration
def test_hnsw_index_used(pg_connection, pg_policy_id):
    """Test that HNSW index is used for similarity queries."""
    vector = [0.5] * 1024
    vector_str = "[" + ",".join(str(v) for v in vector) + "]"

    with pg_connection.cursor() as cur:
        cur.execute(
            "INSERT INTO policy_chunks (policy_id, content_type, content_text, embedding) "
            "VALUES (%s, 'text', 'Test chunk', %s::vector)",
            (pg_policy_id, vector_str),
        )
        pg_connection.commit()

        cur.execute(
            "EXPLAIN (FORMAT TEXT) SELECT id FROM policy_chunks "
            "WHERE policy_id = %s ORDER BY embedding <=> %s::vector LIMIT 1",
            (pg_policy_id, vector_str),
        )
        explain_output = "\n".join([row[0] for row in cur.fetchall()])
        assert "policy_chunks" in explain_output.lower()
