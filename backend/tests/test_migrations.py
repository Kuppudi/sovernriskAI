from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from backend.app.core.config import get_settings


def test_migrations_upgrade_downgrade_and_match_models(tmp_path, monkeypatch):
    # Local fallback test. CI also runs the complete suite against PostgreSQL.
    url = f"sqlite:///{tmp_path / 'migration.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    config = Config("alembic.ini")
    try:
        command.upgrade(config, "head")
        engine = create_engine(url)
        assert "observations" in inspect(engine).get_table_names()
        command.check(config)
        engine.dispose()
        command.downgrade(config, "base")
        engine = create_engine(url)
        assert "observations" not in inspect(engine).get_table_names()
        engine.dispose()
    finally:
        get_settings.cache_clear()
