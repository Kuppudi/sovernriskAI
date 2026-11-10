"""Check what will be shipped to Azure, without deploying anything."""

import os
import subprocess
import sys
from zipfile import ZipFile

import pytest

from scripts.package_app_service import (
    APP_FILES,
    APP_FOLDERS,
    PROJECT_ROOT,
    create_package,
)


@pytest.fixture
def project(tmp_path):
    for folder in APP_FOLDERS:
        (tmp_path / folder).mkdir(parents=True)
    files = [
        *APP_FILES,
        "backend/app/main.py",
        "frontend/dist/index.html",
        "frontend/dist/assets/app.js",
        "frontend/dist/maps/world-countries.json",
    ]
    for name in files:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Synthetic packaging fixture")
    return tmp_path


def test_package_contains_the_whole_app_but_not_local_secrets(project):
    for name in [
        ".env",
        "data/raw/download.json",
        "frontend/node_modules/example/index.js",
        "backend/app/__pycache__/main.pyc",
        "backend/app/.env",
    ]:
        path = project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Must not be deployed")

    output = project / "dist" / "app-service.zip"
    create_package(project, output)
    with ZipFile(output) as archive:
        names = archive.namelist()
    assert "backend/app/main.py" in names
    assert "frontend/dist/index.html" in names
    assert "frontend/dist/assets/app.js" in names
    assert "frontend/dist/maps/world-countries.json" in names
    assert "requirements.txt" in names and "startup.sh" in names
    assert not any(
        ".env" in name
        or "node_modules" in name
        or "__pycache__" in name
        or name.startswith("data/")
        for name in names
    )


@pytest.mark.parametrize(
    "missing",
    [
        "frontend/dist/index.html",
        "frontend/dist/assets/app.js",
        "frontend/dist/maps/world-countries.json",
    ],
)
def test_incomplete_frontend_build_cannot_be_packaged(project, missing):
    (project / missing).unlink()
    with pytest.raises(ValueError):
        create_package(project, project / "dist" / "app-service.zip")


def test_package_cannot_include_itself(project):
    with pytest.raises(ValueError):
        create_package(project, project / "frontend" / "dist" / "app-service.zip")


def test_package_rejects_symlinked_source_files(project, tmp_path_factory):
    external_file = tmp_path_factory.mktemp("outside-project") / "secret.txt"
    external_file.write_text("Synthetic secret fixture")
    (project / "requirements.txt").unlink()
    (project / "requirements.txt").symlink_to(external_file)
    with pytest.raises(ValueError):
        create_package(project, project / "dist" / "app-service.zip")


def test_startup_explains_a_missing_frontend_build(tmp_path):
    script = tmp_path / "startup.sh"
    script.write_text((PROJECT_ROOT / "startup.sh").read_text())
    result = subprocess.run(["bash", str(script)], capture_output=True, text=True)
    assert result.returncode == 1
    assert "Frontend build missing" in result.stderr


@pytest.mark.skipif(
    not (PROJECT_ROOT / "frontend/dist/index.html").exists(),
    reason="Run npm run build first; the App Service CI job does this.",
)
def test_real_frontend_and_api_run_from_the_extracted_package(tmp_path):
    output = tmp_path / "app-service.zip"
    create_package(PROJECT_ROOT, output)
    unpacked = tmp_path / "unpacked"
    with ZipFile(output) as archive:
        archive.extractall(unpacked)

    # A fresh Python process verifies the packaged files, not the source checkout.
    check = """
from pathlib import Path
import re
from fastapi.testclient import TestClient
import backend.app.main as server
assert Path(server.__file__).resolve().is_relative_to(Path.cwd())
with TestClient(server.app) as client:
    page = client.get("/")
    assert page.status_code == 200 and "SovereignRisk AI" in page.text
    for asset in re.findall(r'(?:src|href)="(/assets/[^\"]+)"', page.text):
        assert client.get(asset).status_code == 200
    assert client.get("/countries/IND").text == page.text
    assert client.get("/maps/world-countries.json").status_code == 200
    assert client.get("/api/models/status").json()["status"] == "unavailable"
    assert client.get("/api/missing").status_code == 404
    assert client.get("/assets/missing.js").status_code == 404
"""
    environment = {
        **os.environ,
        "PYTHONPATH": str(unpacked),
        "FRONTEND_DIR": str(unpacked / "frontend/dist"),
    }
    result = subprocess.run(
        [sys.executable, "-c", check],
        cwd=unpacked,
        env=environment,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
