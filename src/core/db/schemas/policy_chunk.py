"""SQLAlchemy ORM model for the policy_chunks table."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.schemas.base import Base

if TYPE_CHECKING:
    from core.db.schemas.policy import Policy


class PolicyChunk(Base):
    __tablename__ = "policy_chunks"

    id: Mapped[str] = mapped_column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))
    policy_id: Mapped[str] = mapped_column(UUID, ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    content_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content_text: Mapped[str | None] = mapped_column(Text)
    source_page: Mapped[int | None] = mapped_column(Integer)
    section_title: Mapped[str | None] = mapped_column(String(255))
    reading_order: Mapped[int | None] = mapped_column(Integer)
    bda_entity_id: Mapped[str | None] = mapped_column(String(255))
    bda_entity_subtype: Mapped[str | None] = mapped_column(String(50))
    embedding = mapped_column(Vector(1024), nullable=False)
    metadata_ = mapped_column("metadata", JSONB)
    created_at = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"))

    policy: Mapped["Policy"] = relationship(back_populates="chunks")

    __table_args__ = (
        CheckConstraint("content_type IN ('text', 'table', 'figure')", name="chk_content_type"),
        Index("idx_policy_chunks_policy_id", "policy_id"),
        Index("idx_policy_chunks_content_type", "content_type"),
    )

