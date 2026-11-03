"""All values in these fixtures are SYNTHETIC and isolated from application data."""

import asyncio
import os
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.session import Base, get_db
from backend.app.main import app


@pytest.fixture
def engine():
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        admin = create_engine(url)
        schema = "test_" + uuid4().hex
        with admin.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        test_url = make_url(url).update_query_dict(
            {"options": f"-csearch_path={schema}"}
        )
        engine = create_engine(test_url)
    else:
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )

        @event.listens_for(engine, "connect")
        def enforce_foreign_keys(connection, record):
            connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()
    if url:
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


@pytest.fixture
def db(engine):
    with Session(engine) as session:
        yield session


def synthetic_handler(*, changed=False, invalid=False, missing=False, fail=False):
    """Synthetic API responses; never used by the development application."""

    def handler(request):
        path = request.url.path
        if fail:
            return httpx.Response(500)
        meta = {"page": 1, "pages": 1, "total": 1, "lastupdated": "2025-01-01"}
        if path.endswith("country/all"):
            rows = [
                {
                    "id": code,
                    "name": f"Synthetic {code}",
                    "region": {"id": "TST", "value": "Test Region"},
                    "incomeLevel": {"value": "Test Income"},
                }
                for code in ["USA", "IND"]
            ]
            rows.append(
                {"id": "WLD", "name": "Synthetic aggregate", "region": {"id": "NA"}}
            )
        elif "/country/" not in path:
            code = path.split("/")[-1]
            rows = [
                {
                    "id": code,
                    "name": "Synthetic " + code,
                    "sourceNote": "Synthetic fixture definition.",
                }
            ]
        else:
            code = path.split("/")[-1]
            rows = [
                {
                    "countryiso3code": country,
                    "indicator": {"id": code},
                    "date": str(year),
                    "value": None
                    if code == "FP.CPI.TOTL.ZG"
                    or (changed and year == 2024 and code == "NY.GDP.MKTP.KD.ZG")
                    else 0
                    if year == 2023
                    else 2.5,
                }
                for country in ["USA", "IND"]
                for year in [2023, 2024]
            ]
            if invalid:
                rows[0]["value"] = "not numeric"
            if missing:
                rows = rows[:-1]
        meta["total"] = len(rows)
        return httpx.Response(200, json=[meta, rows])

    return handler


def ingest_fixture(db, tmp_path, **options):
    from ingestion.connectors.world_bank import WorldBankClient
    from ingestion.pipelines.world_bank import ingest_world_bank

    async def run():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(synthetic_handler(**options))
        ) as client:
            return await ingest_world_bank(
                db,
                WorldBankClient(client, retries=0),
                ["USA", "IND"],
                2023,
                2024,
                tmp_path,
            )

    return asyncio.run(run())


@pytest.fixture
def populated(db, tmp_path):
    ingest_fixture(db, tmp_path)
    return db


@pytest.fixture
def client(db):
    def override():
        yield db

    app.dependency_overrides[get_db] = override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
