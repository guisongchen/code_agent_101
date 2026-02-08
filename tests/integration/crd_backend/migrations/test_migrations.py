"""Tests for Alembic database migrations.

Tests: 5 tests covering migration functionality
"""

import os
import tempfile

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Use file-based SQLite for migration tests (required for Alembic)
TEST_DB_FILE = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE.name}"
ALEMBIC_INI_PATH = "/home/ccc/vibe_projects/code_agent_101/alembic.ini"


@pytest.fixture
def alembic_cfg():
    """Create Alembic configuration."""
    cfg = Config(ALEMBIC_INI_PATH)
    cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    return cfg


@pytest.fixture
def db_engine():
    """Create a database engine."""
    engine = create_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def cleanup_db():
    """Clean up the test database file after each test."""
    yield
    # Clean up after test
    if os.path.exists(TEST_DB_FILE.name):
        os.unlink(TEST_DB_FILE.name)


@pytest.mark.epic_7
@pytest.mark.integration
@pytest.mark.backend
class TestMigrations:
    """Test suite for Alembic migrations - 5 tests."""

    def test_migration_upgrade(self, alembic_cfg, db_engine):
        """Test that migrations can be applied successfully."""
        # Run upgrade
        command.upgrade(alembic_cfg, "head")

        # Verify tables exist
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        assert "kinds" in tables
        assert "tasks" in tables

    def test_migration_downgrade(self, alembic_cfg, db_engine):
        """Test that migrations can be reverted."""
        # First upgrade
        command.upgrade(alembic_cfg, "head")

        # Then downgrade
        command.downgrade(alembic_cfg, "base")

        # Verify tables are removed
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        assert "kinds" not in tables
        assert "tasks" not in tables

    def test_kinds_table_schema(self, alembic_cfg, db_engine):
        """Test that kinds table has correct schema."""
        command.upgrade(alembic_cfg, "head")

        inspector = inspect(db_engine)
        columns = {col["name"]: col for col in inspector.get_columns("kinds")}

        # Check required columns exist
        assert "id" in columns
        assert "kind" in columns
        assert "api_version" in columns
        assert "name" in columns
        assert "namespace" in columns
        assert "spec" in columns
        assert "created_by" in columns
        assert "created_at" in columns
        assert "updated_at" in columns
        assert "deleted_at" in columns

        # Check id is primary key
        pk = inspector.get_pk_constraint("kinds")
        assert "id" in pk["constrained_columns"]

    def test_tasks_table_schema(self, alembic_cfg, db_engine):
        """Test that tasks table has correct schema."""
        command.upgrade(alembic_cfg, "head")

        inspector = inspect(db_engine)
        columns = {col["name"]: col for col in inspector.get_columns("tasks")}

        # Check required columns exist
        assert "id" in columns
        assert "name" in columns
        assert "namespace" in columns
        assert "status" in columns
        assert "team_id" in columns
        assert "input" in columns
        assert "output" in columns
        assert "error" in columns
        assert "spec" in columns
        assert "started_at" in columns
        assert "completed_at" in columns
        assert "created_by" in columns
        assert "created_at" in columns
        assert "updated_at" in columns
        assert "deleted_at" in columns

        # Check foreign key
        fks = inspector.get_foreign_keys("tasks")
        assert len(fks) == 1
        assert fks[0]["referred_table"] == "kinds"
        assert "team_id" in fks[0]["constrained_columns"]

    def test_migration_idempotency(self, alembic_cfg, db_engine):
        """Test that running migrations multiple times is safe."""
        # Run upgrade twice
        command.upgrade(alembic_cfg, "head")
        command.upgrade(alembic_cfg, "head")  # Should be idempotent

        # Verify tables still exist and have data capability
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        assert "kinds" in tables
        assert "tasks" in tables

        # Verify we can insert data
        Session = sessionmaker(bind=db_engine)
        session = Session()

        # Insert test data using raw SQL for simplicity
        from sqlalchemy import text

        session.execute(
            text("""
            INSERT INTO kinds (id, kind, api_version, name, namespace, spec)
            VALUES ('12345678-1234-1234-1234-123456789abc', 'ghost', 'v1', 'test', 'default', '{}')
        """)
        )
        session.commit()

        result = session.execute(text("SELECT COUNT(*) FROM kinds"))
        count = result.scalar()
        assert count == 1

        session.close()
