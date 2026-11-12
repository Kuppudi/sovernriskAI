"""Execute notebook cells against synthetic APIs and isolated files/databases only."""

import ast
import asyncio
import copy
import inspect
import json
from pathlib import Path

import httpx
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

pd = pytest.importorskip(
    "pandas", reason="Install notebooks/requirements.txt for notebook tests"
)
pytest.importorskip("IPython")
nbformat = pytest.importorskip("nbformat")

from backend.app.models import DataSnapshot, IngestionRun, Observation
from backend.app.db.session import Base
from ingestion.indicators import INDICATORS

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "notebooks" / "data_extract.ipynb"
REAL_ASYNC_CLIENT = httpx.AsyncClient


def synthetic_world_bank(request, *, changed=False, incomplete=False):
    path = request.url.path
    if path.endswith("country/all"):
        rows = [
            {
                "id": country,
                "name": f"Synthetic {country}",
                "region": {"id": "TST", "value": "Synthetic region"},
                "incomeLevel": {"value": "Synthetic income"},
            }
            for country in ["USA", "IND"]
        ]
        rows.append({"id": "WLD", "region": {"id": "NA"}})
    elif "/country/" not in path:
        code = path.split("/")[-1]
        rows = [
            {
                "id": code,
                "name": f"Synthetic {code}",
                "sourceNote": "Synthetic definition",
            }
        ]
    else:
        code = path.split("/")[-1]
        first, last = map(int, request.url.params["date"].split(":"))
        rows = []
        for country in path.split("/")[-3].split(";"):
            for year in range(first, last + 1):
                value = 0 if year == 2023 else 2.5
                if code == "FP.CPI.TOTL.ZG":
                    value = None
                if changed and code == "NY.GDP.MKTP.KD.ZG" and year == 2024:
                    value = None
                rows.append(
                    {
                        "countryiso3code": country,
                        "indicator": {"id": code},
                        "date": str(year),
                        "value": value,
                    }
                )
        if incomplete:
            rows.pop()
    return httpx.Response(
        200,
        json=[
            {"page": 1, "pages": 1, "total": len(rows), "lastupdated": "2025-01-01"},
            rows,
        ],
    )


def run_notebook(
    tmp_path,
    monkeypatch,
    *,
    changed=False,
    incomplete=False,
    full_refresh=True,
    preview=False,
    load=False,
    before_export=None,
):
    """The test transport prevents these notebook runs from contacting any API."""
    monkeypatch.chdir(ROOT)
    requests = []

    def handler(request):
        requests.append(request)
        return synthetic_world_bank(request, changed=changed, incomplete=incomplete)

    def fixture_client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return REAL_ASYNC_CLIENT(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", fixture_client)
    notebook = json.loads(NOTEBOOK.read_text())
    namespace = {"__name__": "notebook_fixture"}

    async def execute():
        for cell in notebook["cells"]:
            if cell["cell_type"] != "code":
                continue
            source = "".join(cell["source"])
            if cell["id"] == "database-preview" and preview:
                source = source.replace(
                    "PREVIEW_DATABASE_TARGET = False", "PREVIEW_DATABASE_TARGET = True"
                )
            if cell["id"] == "database-load" and load:
                source = source.replace(
                    "LOAD_TO_DATABASE = False", "LOAD_TO_DATABASE = True"
                )
            if cell["id"] == "export" and before_export:
                before_export(namespace)
            compiled = compile(
                source,
                f"notebook:{cell['id']}",
                "exec",
                flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
            )
            result = eval(compiled, namespace)
            if inspect.isawaitable(result):
                await result
            if cell["id"] == "parameters":
                namespace.update(
                    {
                        "COUNTRIES": ["USA", "IND"],
                        "START_YEAR": 2023,
                        "END_YEAR": 2024,
                        "OUTPUT_ROOT": tmp_path,
                        "FULL_REFRESH": full_refresh,
                        "REFRESH_LOOKBACK_YEARS": 1,
                    }
                )

    asyncio.run(execute())
    return namespace, requests


def test_notebook_is_valid_and_saved_without_outputs():
    book = nbformat.read(NOTEBOOK, as_version=4)
    nbformat.validate(book)
    for cell in book.cells:
        if cell.cell_type == "code":
            assert cell.execution_count is None
            assert cell.outputs == []
    text = NOTEBOOK.read_text()
    assert "PREVIEW_DATABASE_TARGET = False" in text
    assert "LOAD_TO_DATABASE = False" in text


def test_files_only_ignores_invalid_database_setting(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", "invalid://never-print-this-password")
    namespace, requests = run_notebook(tmp_path, monkeypatch)
    assert len(requests) == 19
    assert len(namespace["silver"]) == 24
    assert len(namespace["country_year"]) == 4
    assert len(namespace["coverage"]) == 12
    assert namespace["silver"]["value"].eq(0).sum() == 10
    assert namespace["silver"]["value"].isna().sum() == 4
    assert namespace["coverage"]["absent_rows"].sum() == 0
    assert namespace["database_url_for_load"] is None
    assert "never-print-this-password" not in capsys.readouterr().out
    raw = json.loads(namespace["bronze_path"].read_text())
    assert len(raw["pages"]) == 19
    assert "WLD" not in set(namespace["silver"]["country_iso3"])
    assert namespace["silver"]["publication_date"].isna().all()


def test_repeat_run_reuses_versioned_outputs(tmp_path, monkeypatch):
    first, _ = run_notebook(tmp_path, monkeypatch)
    second, _ = run_notebook(tmp_path, monkeypatch)
    assert first["dataset_version"] == second["dataset_version"]
    assert first["run_id"] != second["run_id"]
    assert len(list((tmp_path / "silver").iterdir())) == 1
    assert len(list((tmp_path / "runs").iterdir())) == 2


def test_incremental_null_revision_replaces_current_value_and_keeps_old_snapshot(
    tmp_path, monkeypatch
):
    first, _ = run_notebook(tmp_path, monkeypatch)
    old_path = first["silver_folder"] / "dataset.json"
    old_bytes = old_path.read_bytes()
    second, requests = run_notebook(
        tmp_path, monkeypatch, full_refresh=False, changed=True
    )
    assert second["fetch_start_year"] == 2024
    assert len(second["downloaded"]["observations"]) == 12
    assert len(second["dataset"]["observations"]) == 24
    assert first["dataset_version"] != second["dataset_version"]
    assert old_path.read_bytes() == old_bytes
    assert second["run_record"]["previous_dataset_version"] == first["dataset_version"]
    revised = second["silver"].query(
        "indicator_code == 'NY.GDP.MKTP.KD.ZG' and year == 2024"
    )
    assert revised["value"].isna().all()
    assert all(
        request.url.params["date"] == "2024:2024"
        for request in requests
        if "date" in request.url.params
    )


def test_incomplete_api_result_is_archived_without_advancing_checkpoint(
    tmp_path, monkeypatch
):
    first, _ = run_notebook(tmp_path, monkeypatch)
    old_state = first["state_path"].read_bytes()
    with pytest.raises(RuntimeError, match="extraction failed"):
        run_notebook(tmp_path, monkeypatch, incomplete=True, full_refresh=False)
    assert first["state_path"].read_bytes() == old_state
    runs = [json.loads(path.read_text()) for path in (tmp_path / "runs").glob("*.json")]
    failed = next(run for run in runs if run["status"] == "failed")
    assert (tmp_path / "bronze" / failed["run_id"] / "responses.json").exists()


@pytest.mark.parametrize("failure", ["export", "checkpoint"])
def test_publication_failure_keeps_previous_checkpoint_and_audits_failure(
    tmp_path, monkeypatch, failure
):
    first, _ = run_notebook(tmp_path, monkeypatch)
    old_state = first["state_path"].read_bytes()

    def inject_failure(namespace):
        if failure == "export":

            def fail_write(*args, **kwargs):
                raise OSError("Synthetic export failure")

            namespace["write_versioned_text"] = fail_write
        else:
            original_writer = namespace["write_json"]

            def fail_checkpoint(path, value):
                if path == namespace["state_path"]:
                    raise OSError("Synthetic checkpoint failure")
                original_writer(path, value)

            namespace["write_json"] = fail_checkpoint

    with pytest.raises(RuntimeError, match="publication failed"):
        run_notebook(
            tmp_path,
            monkeypatch,
            changed=True,
            full_refresh=False,
            before_export=inject_failure,
        )
    assert first["state_path"].read_bytes() == old_state
    runs = [json.loads(path.read_text()) for path in (tmp_path / "runs").glob("*.json")]
    assert any(
        run["status"] == "failed" and run["error_type"] == "OSError" for run in runs
    )


def test_database_preview_is_credential_free_and_does_not_load(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://student:never-print-this-password@example.test:5432/learning",
    )
    namespace, _ = run_notebook(tmp_path, monkeypatch, preview=True)
    assert namespace["database_target"] == {
        "host": "example.test",
        "port": 5432,
        "database": "learning",
    }
    assert "never-print-this-password" not in capsys.readouterr().out


def test_database_load_requires_a_reviewed_preview(tmp_path, monkeypatch):
    with pytest.raises(RuntimeError, match="preview cell"):
        run_notebook(tmp_path, monkeypatch, load=True)


def test_optional_load_reuses_extraction_and_is_idempotent(
    tmp_path, monkeypatch, engine
):
    namespace, requests = run_notebook(tmp_path, monkeypatch)
    loader = namespace["load_extracted_data"]
    url = engine.url.render_as_string(hide_password=False)
    if engine.dialect.name == "sqlite":
        # A file lets the notebook open its own connection to this isolated test DB.
        url = f"sqlite:///{tmp_path / 'notebook-test.db'}"
        setup_engine = create_engine(url)
        Base.metadata.create_all(setup_engine)
        setup_engine.dispose()
    first = loader(
        namespace["dataset"],
        namespace["connector"].raw_pages,
        url,
        tmp_path / "db_archives",
    )
    second = loader(
        namespace["dataset"],
        namespace["connector"].raw_pages,
        url,
        tmp_path / "db_archives",
    )
    assert first["dataset_version"] == second["dataset_version"]
    assert first["run_id"] != second["run_id"]
    assert len(requests) == 19
    verification_engine = create_engine(url)
    try:
        with Session(verification_engine) as db:
            assert db.scalar(select(func.count()).select_from(Observation)) == 24
            assert db.scalar(select(func.count()).select_from(DataSnapshot)) == 1
            assert db.scalar(select(func.count()).select_from(IngestionRun)) == 2
    finally:
        verification_engine.dispose()


def test_optional_load_sanitizes_database_errors(tmp_path, monkeypatch):
    namespace, _ = run_notebook(tmp_path, monkeypatch)
    with pytest.raises(RuntimeError) as error:
        namespace["load_extracted_data"](
            namespace["dataset"], [], "invalid://private-password", tmp_path
        )
    assert "private-password" not in str(error.value)


def test_dataset_contract_rejects_duplicates_and_missing_rows(tmp_path, monkeypatch):
    namespace, _ = run_notebook(tmp_path, monkeypatch)
    dataset = copy.deepcopy(namespace["dataset"])
    dataset["observations"].append(dataset["observations"][0])
    with pytest.raises(ValueError, match="Duplicate"):
        namespace["validate_dataset"](dataset, ["USA", "IND"], 2023, 2024)
    dataset["observations"] = dataset["observations"][:-2]
    with pytest.raises(ValueError, match="Incomplete"):
        namespace["validate_dataset"](dataset, ["USA", "IND"], 2023, 2024)
