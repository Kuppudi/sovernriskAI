"""Use isolated HTML/JS fixtures to check the shared frontend/API server."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.routes import router
from backend.app.frontend import add_frontend_routes


@pytest.fixture
def website(tmp_path):
    (tmp_path / "index.html").write_text("<html>Synthetic frontend fixture</html>")
    (tmp_path / "favicon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("// Synthetic test asset")
    (tmp_path / "maps").mkdir()
    (tmp_path / "maps" / "world-countries.json").write_text(
        '{"type":"FeatureCollection","features":[]}'
    )
    app = FastAPI()
    app.include_router(router)
    add_frontend_routes(app, tmp_path)
    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize(
    "url",
    [
        "/",
        "/countries",
        "/countries/IND",
        "/compare",
        "/reports?country=USA",
        "/explorer",
    ],
)
def test_pages_support_direct_links_and_refresh(website, url):
    response = website.get(url)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Synthetic frontend fixture" in response.text
    assert response.headers["cache-control"] == "no-cache"


def test_files_and_api_share_one_server(website):
    assert website.get("/assets/app.js").text == "// Synthetic test asset"
    assert website.get("/maps/world-countries.json").json()["features"] == []
    assert website.get("/favicon.svg").status_code == 200
    assert website.get("/api/models/status").json()["status"] == "unavailable"
    assert "/api/countries" in website.get("/openapi.json").json()["paths"]
    assert "/" not in website.get("/openapi.json").json()["paths"]
    assert website.get("/docs").status_code == 200


@pytest.mark.parametrize(
    "url",
    [
        "/api/unknown",
        "/assets/missing.js",
        "/maps/missing.json",
        "/unknown",
        "/assets/%2e%2e/%2e%2e/.env",
    ],
)
def test_missing_files_and_api_routes_do_not_return_the_react_page(website, url):
    response = website.get(url)
    assert response.status_code == 404
    assert "Synthetic frontend fixture" not in response.text


def test_backend_development_does_not_require_a_frontend_build(tmp_path):
    app = FastAPI()
    app.include_router(router)
    add_frontend_routes(app, tmp_path / "not-built")
    with TestClient(app) as client:
        assert client.get("/api/models/status").status_code == 200
        assert client.get("/").status_code == 404
