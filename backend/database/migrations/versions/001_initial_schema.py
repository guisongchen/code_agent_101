"""Initial schema for CRD kinds and tasks tables.

Revision ID: 001
Revises:
Create Date: 2026-02-08 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the initial database schema."""
    # Get the dialect
    dialect = op.get_bind().dialect.name

    # Create enum types only for PostgreSQL
    if dialect == "postgresql":
        kind_type_enum = postgresql.ENUM(
            "ghost", "model", "shell", "bot", "team", "skill",
            name="kind_type_enum",
            create_type=True,
        )
        kind_type_enum.create(op.get_bind())

        task_status_enum = postgresql.ENUM(
            "pending", "running", "completed", "failed", "cancelled",
            name="task_status_enum",
            create_type=True,
        )
        task_status_enum.create(op.get_bind())

    # Define column types based on dialect
    if dialect == "postgresql":
        uuid_type = postgresql.UUID(as_uuid=True)
        kind_enum = sa.Enum(
            "GHOST", "MODEL", "SHELL", "BOT", "TEAM", "SKILL",
            name="kind_type_enum",
            native_enum=True,
        )
        status_enum = sa.Enum(
            "PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED",
            name="task_status_enum",
            native_enum=True,
        )
        server_default_now = sa.text("now()")
    else:
        # SQLite fallback
        uuid_type = sa.String(36)
        kind_enum = sa.String(20)
        status_enum = sa.String(20)
        server_default_now = sa.text("CURRENT_TIMESTAMP")

    # Create kinds table
    op.create_table(
        "kinds",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("kind", kind_enum, nullable=False),
        sa.Column("api_version", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("namespace", sa.String(length=255), nullable=False),
        sa.Column("spec", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=server_default_now,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=server_default_now,
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("kind", "name", "namespace", name="uix_kind_name_namespace"),
    )

    # Create indexes for kinds table
    op.create_index("ix_kinds_kind", "kinds", ["kind"])
    op.create_index("ix_kinds_kind_namespace", "kinds", ["kind", "namespace"])
    op.create_index("ix_kinds_created_by", "kinds", ["created_by"])
    op.create_index("ix_kinds_deleted_at", "kinds", ["deleted_at"])

    # Create tasks table
    op.create_table(
        "tasks",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("namespace", sa.String(length=255), nullable=False),
        sa.Column("status", status_enum, nullable=False),
        sa.Column("team_id", uuid_type, nullable=True),
        sa.Column("input", sa.Text(), nullable=True),
        sa.Column("output", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("spec", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=server_default_now,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=server_default_now,
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["kinds.id"],
            ondelete="SET NULL",
        ),
    )

    # Create indexes for tasks table
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_status_namespace", "tasks", ["status", "namespace"])
    op.create_index("ix_tasks_team_id", "tasks", ["team_id"])
    op.create_index("ix_tasks_created_by", "tasks", ["created_by"])
    op.create_index("ix_tasks_deleted_at", "tasks", ["deleted_at"])


def downgrade() -> None:
    """Drop the database schema."""
    # Get the dialect
    dialect = op.get_bind().dialect.name

    # Drop tasks table and indexes
    op.drop_index("ix_tasks_deleted_at", table_name="tasks")
    op.drop_index("ix_tasks_created_by", table_name="tasks")
    op.drop_index("ix_tasks_team_id", table_name="tasks")
    op.drop_index("ix_tasks_status_namespace", table_name="tasks")
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_table("tasks")

    # Drop kinds table and indexes
    op.drop_index("ix_kinds_deleted_at", table_name="kinds")
    op.drop_index("ix_kinds_created_by", table_name="kinds")
    op.drop_index("ix_kinds_kind_namespace", table_name="kinds")
    op.drop_index("ix_kinds_kind", table_name="kinds")
    op.drop_table("kinds")

    # Drop enum types only for PostgreSQL
    if dialect == "postgresql":
        op.execute("DROP TYPE IF EXISTS task_status_enum")
        op.execute("DROP TYPE IF EXISTS kind_type_enum")
