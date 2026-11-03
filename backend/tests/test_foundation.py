"""API behavior that works before any economic data is imported."""

import pytest


def test_health_and_empty_freshness(client):
    assert client.get("/health").json()["database"] == "connected"
    response = client.get("/api/data/freshness").json()
    assert response["latest_successful_refresh"] is None
    assert response["latest_observation_year"] is None
    assert response["countries_with_data"] == 0


@pytest.mark.parametrize(
    "url,code",
    [
        ("/api/countries/US", 422),
        ("/api/countries/ZZZ", 404),
        ("/api/countries?limit=10000", 422),
    ],
)
def test_invalid_country_and_pagination(client, url, code):
    response = client.get(url)
    assert response.status_code == code
    assert "error" in response.json()


def test_cors_only_allows_configured_origins(client):
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
    }
    assert (
        client.options("/api/countries", headers=headers).headers[
            "access-control-allow-origin"
        ]
        == "http://localhost:5173"
    )
    headers["Origin"] = "https://unknown.example"
    assert (
        "access-control-allow-origin"
        not in client.options("/api/countries", headers=headers).headers
    )
