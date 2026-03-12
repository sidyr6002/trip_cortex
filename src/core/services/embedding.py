"""Service for generating Nova MME embeddings from BDA output."""

import json
from typing import Any

import structlog

from core.db.aurora import AuroraClient
from core.errors import ErrorCode, PolicyRetrievalError
from core.models.ingestion import BdaEntity, EmbeddingResult, FailedEntity

logger = structlog.get_logger()


class EmbeddingService:
    """Generates Nova MME embeddings from BDA output and stores in pgvector."""

    def __init__(
        self,
        bedrock_runtime_client: Any,
        s3_client: Any,
        aurora_client: AuroraClient,
        model_id: str,
    ) -> None:
        self.bedrock_runtime_client = bedrock_runtime_client
        self.s3_client = s3_client
        self.aurora_client = aurora_client
        self.model_id = model_id

    def generate_embeddings(self, policy_id: str, bda_output_s3_uri: str) -> EmbeddingResult:
        """
        Parse BDA output, generate embeddings, and insert into policy_chunks.

        Args:
            policy_id: UUID of the policy
            bda_output_s3_uri: S3 URI prefix for BDA output

        Returns:
            EmbeddingResult with chunks created/failed counts and failed entities

        Raises:
            PolicyRetrievalError: If S3 read or DB operation fails
        """
        try:
            entities = self._parse_bda_output(bda_output_s3_uri)
        except Exception as e:
            raise PolicyRetrievalError(
                f"Failed to parse BDA output: {e}",
                code=ErrorCode.RETRIEVAL_FAILED,
            ) from e

        chunks = []
        failed_entities = []
        entity_types_count: dict[str, int] = {}

        for entity in entities:
            try:
                vector, content_type = self._embed_entity(entity)
                chunks.append(
                    {
                        "policy_id": policy_id,
                        "content_type": content_type,
                        "content_text": entity.content_text or entity.markdown or "",
                        "source_page": entity.page_index,
                        "section_title": entity.section_title,
                        "reading_order": entity.reading_order,
                        "bda_entity_id": entity.entity_id,
                        "bda_entity_subtype": entity.sub_type,
                        "embedding": vector,
                        "metadata": json.dumps({"bounding_box": entity.bounding_box}),
                    }
                )
                entity_types_count[content_type] = entity_types_count.get(content_type, 0) + 1
            except Exception as e:
                failed_entities.append(
                    FailedEntity(
                        entity_id=entity.entity_id,
                        entity_type=entity.entity_type,
                        error=str(e),
                    )
                )
                logger.warning(
                    "entity_embedding_failed",
                    entity_id=entity.entity_id,
                    entity_type=entity.entity_type,
                    error=str(e),
                )

        chunks_created = self.aurora_client.insert_chunks(chunks)
        self.aurora_client.update_policy_status(policy_id, "embedded", chunks_created)

        logger.info(
            "chunks_stored",
            policy_id=policy_id,
            chunks_created=chunks_created,
            chunks_failed=len(failed_entities),
            entity_types=entity_types_count,
        )

        return EmbeddingResult(
            policy_id=policy_id,
            chunks_created=chunks_created,
            chunks_failed=len(failed_entities),
            entity_types=entity_types_count,
            failed_entities=failed_entities,
        )

    def _parse_bda_output(self, bda_output_s3_uri: str) -> list[BdaEntity]:
        """Parse BDA result JSON from S3 and extract entities."""
        # Extract bucket and prefix from S3 URI
        # BDA returns a URI pointing to job_metadata.json — strip the filename to get the dir prefix
        uri_parts = bda_output_s3_uri.replace("s3://", "").split("/", 1)
        bucket = uri_parts[0]
        raw_prefix = uri_parts[1] if len(uri_parts) > 1 else ""
        # Strip trailing filename if present (BDA returns path to job_metadata.json)
        prefix = raw_prefix.rsplit("/", 1)[0] + "/" if "/" in raw_prefix else raw_prefix

        # List objects to find result.json
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        except Exception as e:
            raise PolicyRetrievalError(
                f"Failed to list S3 objects: {e}",
                code=ErrorCode.RETRIEVAL_FAILED,
            ) from e

        result_json_key = None
        for obj in response.get("Contents", []):
            if obj["Key"].endswith("result.json"):
                result_json_key = obj["Key"]
                break

        if not result_json_key:
            raise PolicyRetrievalError(
                "No result.json found in BDA output",
                code=ErrorCode.RETRIEVAL_FAILED,
            )

        # Read and parse result.json
        try:
            obj = self.s3_client.get_object(Bucket=bucket, Key=result_json_key)
            bda_output = json.loads(obj["Body"].read())
        except Exception as e:
            raise PolicyRetrievalError(
                f"Failed to read BDA result.json: {e}",
                code=ErrorCode.RETRIEVAL_FAILED,
            ) from e

        entities = []
        for entity_data in bda_output.get("elements", []):
            entity_type = entity_data.get("type")
            if entity_type == "PAGE":
                continue

            representation = entity_data.get("representation", {})
            content_text = None
            markdown = None

            if entity_type in ("TEXT", "TABLE"):
                markdown = representation.get("markdown") or representation.get("text")
                content_text = representation.get("text")
            elif entity_type == "FIGURE":
                content_text = entity_data.get("summary") or entity_data.get("title")

            crop_image_s3_uri = None
            if entity_type == "FIGURE":
                crop_images = entity_data.get("crop_images", [])
                if crop_images:
                    crop_image_s3_uri = crop_images[0]

            locations = entity_data.get("locations", [])
            page_index = None
            bounding_box = None
            if locations:
                page_index = locations[0].get("page_index")
                bounding_box = locations[0].get("bounding_box")

            entity = BdaEntity(
                entity_type=entity_type,
                sub_type=entity_data.get("sub_type"),
                content_text=content_text,
                markdown=markdown,
                crop_image_s3_uri=crop_image_s3_uri,
                page_index=page_index,
                section_title=entity_data.get("title"),
                reading_order=entity_data.get("reading_order"),
                entity_id=entity_data.get("id"),
                bounding_box=bounding_box,
            )
            entities.append(entity)

        return entities

    def _embed_text(self, text: str) -> list[float]:
        """Generate embedding for text using Nova MME."""
        request_body = {
            "taskType": "SINGLE_EMBEDDING",
            "singleEmbeddingParams": {
                "embeddingPurpose": "GENERIC_INDEX",
                "embeddingDimension": 1024,
                "text": {"truncationMode": "END", "value": text},
            },
        }

        try:
            response = self.bedrock_runtime_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                accept="application/json",
                contentType="application/json",
            )
            result = json.loads(response["body"].read())
            return list(result["embeddings"][0]["embedding"])
        except Exception as e:
            raise PolicyRetrievalError(
                f"Text embedding failed: {e}",
                code=ErrorCode.RETRIEVAL_FAILED,
            ) from e

    def _embed_image(self, s3_uri: str) -> list[float]:
        """Generate embedding for image using Nova MME."""
        request_body = {
            "taskType": "SINGLE_EMBEDDING",
            "singleEmbeddingParams": {
                "embeddingPurpose": "GENERIC_INDEX",
                "embeddingDimension": 1024,
                "image": {
                    "detailLevel": "DOCUMENT_IMAGE",
                    "format": "png",
                    "source": {"s3Location": {"uri": s3_uri}},
                },
            },
        }

        try:
            response = self.bedrock_runtime_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                accept="application/json",
                contentType="application/json",
            )
            result = json.loads(response["body"].read())
            return list(result["embeddings"][0]["embedding"])
        except Exception as e:
            raise PolicyRetrievalError(
                f"Image embedding failed: {e}",
                code=ErrorCode.RETRIEVAL_FAILED,
            ) from e

    def _embed_entity(self, entity: BdaEntity) -> tuple[list[float], str]:
        """Generate embedding for entity and return (vector, content_type)."""
        if entity.entity_type == "FIGURE":
            if entity.crop_image_s3_uri:
                return self._embed_image(entity.crop_image_s3_uri), "figure"
            elif entity.content_text:
                return self._embed_text(entity.content_text), "figure"
            else:
                raise PolicyRetrievalError(
                    "Figure has no image or text content",
                    code=ErrorCode.RETRIEVAL_FAILED,
                )

        content = entity.markdown or entity.content_text
        if not content:
            raise PolicyRetrievalError(
                f"Entity {entity.entity_id} has no content",
                code=ErrorCode.RETRIEVAL_FAILED,
            )

        content_type = "table" if entity.entity_type == "TABLE" else "text"
        return self._embed_text(content), content_type
