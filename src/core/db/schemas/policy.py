"""SQLAlchemy ORM model for the policies table."""

from sqlalchemy import CheckConstraint, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.schemas.base import Base


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))
    source_s3_uri: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    bda_project_arn: Mapped[str | None] = mapped_column(String(512))
    bda_invocation_arn: Mapped[str | None] = mapped_column(String(512))
    total_pages: Mapped[int | None] = mapped_column(Integer)
    total_chunks: Mapped[int | None] = mapped_column(Integer, server_default="0")
    uploaded_by: Mapped[str | None] = mapped_column(String(255))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"))
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    chunks: Mapped[list["PolicyChunk"]] = relationship(back_populates="policy", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'processing', 'ready', 'failed')", name="chk_policies_status"),
        Index("idx_policies_status", "status"),
        Index("idx_policies_uploaded_by", "uploaded_by"),
    )


# Avoid circular import — PolicyChunk is resolved by string reference above
from core.db.schemas.policy_chunk import PolicyChunk  # noqa: E402, F401
