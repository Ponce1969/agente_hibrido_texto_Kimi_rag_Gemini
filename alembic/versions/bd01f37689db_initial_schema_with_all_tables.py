"""initial schema with all tables

Revision ID: bd01f37689db
Revises:
Create Date: 2026-04-15 22:23:44.762465

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "bd01f37689db"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all initial tables."""
    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")
        ),
        sa.Column(
            "is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Chat sessions
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("session_name", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("extra_data", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_user_sessions", "chat_sessions", ["user_id", "is_active"])
    op.create_index("idx_created_at", "chat_sessions", ["created_at"])
    op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"])

    # Chat messages
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("message_index", sa.Integer(), nullable=False),
        sa.Column("extra_data", sa.String(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"], ["chat_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_session_messages", "chat_messages", ["session_id", "message_index"]
    )
    op.create_index("idx_timestamp", "chat_messages", ["timestamp"])
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])

    # File uploads
    op.create_table(
        "file_uploads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid_str", sa.String(), nullable=False),
        sa.Column("filename_original", sa.String(), nullable=False),
        sa.Column("filename_saved", sa.String(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("total_pages", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("pages_processed", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("status", sa.String(), nullable=True, server_default="pending"),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_file_uploads_uuid_str", "file_uploads", ["uuid_str"])
    op.create_index("ix_file_uploads_status", "file_uploads", ["status"])

    # File sections
    op.create_table(
        "file_sections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("start_page", sa.Integer(), nullable=False),
        sa.Column("end_page", sa.Integer(), nullable=False),
        sa.Column("char_count", sa.Integer(), nullable=True, server_default="0"),
        sa.ForeignKeyConstraint(["file_id"], ["file_uploads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_file_sections_file_id", "file_sections", ["file_id"])

    # Agent metrics
    op.create_table(
        "agent_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("agent_mode", sa.String(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("estimated_cost", sa.Float(), nullable=True, server_default="0"),
        sa.Column("response_time", sa.Float(), nullable=True, server_default="0"),
        sa.Column("has_rag_context", sa.Boolean(), nullable=True, server_default="0"),
        sa.Column("rag_chunks_used", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("file_id", sa.String(), nullable=True),
        sa.Column("used_bear_search", sa.Boolean(), nullable=True, server_default="0"),
        sa.Column(
            "bear_sources_count", sa.Integer(), nullable=True, server_default="0"
        ),
        sa.Column("model_name", sa.String(), nullable=True, server_default=""),
        sa.Column("user_rating", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_metrics_session_id", "agent_metrics", ["session_id"])
    op.create_index("ix_agent_metrics_agent_mode", "agent_metrics", ["agent_mode"])

    # Daily metrics summary
    op.create_table(
        "daily_metrics_summary",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.String(), nullable=False),
        sa.Column("total_requests", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("total_sessions", sa.Integer(), nullable=True, server_default="0"),
        sa.Column(
            "total_prompt_tokens", sa.Integer(), nullable=True, server_default="0"
        ),
        sa.Column(
            "total_completion_tokens", sa.Integer(), nullable=True, server_default="0"
        ),
        sa.Column("total_tokens", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("total_cost", sa.Float(), nullable=True, server_default="0"),
        sa.Column("avg_response_time", sa.Float(), nullable=True, server_default="0"),
        sa.Column("rag_requests", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("bear_requests", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("agent_usage", sa.String(), nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_daily_metrics_summary_date", "daily_metrics_summary", ["date"])

    # Error logs
    op.create_table(
        "error_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("error_type", sa.String(), nullable=False),
        sa.Column("error_message", sa.String(), nullable=False),
        sa.Column("stack_trace", sa.String(), nullable=True),
        sa.Column("session_id", sa.String(), nullable=True),
        sa.Column("endpoint", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_error_logs_error_type", "error_logs", ["error_type"])

    # Document chunks (pgvector) - only for PostgreSQL
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("section_id", sa.Integer(), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "embedding", postgresql.ARRAY(sa.Float(), dimensions=768), nullable=True
        ),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section_type", sa.String(), nullable=True),
        sa.Column("file_name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_chunks_file_id", "document_chunks", ["file_id"])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("document_chunks")
    op.drop_table("error_logs")
    op.drop_table("daily_metrics_summary")
    op.drop_table("agent_metrics")
    op.drop_table("file_sections")
    op.drop_table("file_uploads")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("users")
