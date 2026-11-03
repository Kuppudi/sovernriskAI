"""Map regressions use only the isolated synthetic data fixture."""

from backend.tests.conftest import ingest_fixture


def test_map_returns_one_exact_year_value_per_country(client, populated):
    response = client.get("/api/data/map?indicator=NY.GDP.MKTP.KD.ZG&year=2024")
    assert response.status_code == 200
    data = response.json()
    assert data["year"] == 2024
    assert data["available_years"] == [2024, 2023]
    assert len(data["countries"]) == 2
    assert all(country["value"] == 2.5 for country in data["countries"])
    assert all(country["observation_year"] == 2024 for country in data["countries"])
    assert all(country["dataset_version"] for country in data["countries"])
    assert data["source_name"] == "World Bank WDI"


def test_map_keeps_zero_values(client, populated):
    data = client.get("/api/data/map?indicator=NY.GDP.MKTP.KD.ZG&year=2023").json()
    assert all(country["value"] == 0 for country in data["countries"])


def test_map_does_not_fill_missing_years_with_older_values(client, populated):
    data = client.get("/api/data/map?indicator=NY.GDP.MKTP.KD.ZG&year=2025").json()
    assert all(country["value"] is None for country in data["countries"])
    assert all(country["observation_year"] is None for country in data["countries"])


def test_map_shows_revised_missing_values(client, populated, tmp_path):
    ingest_fixture(populated, tmp_path, changed=True)
    data = client.get("/api/data/map?indicator=NY.GDP.MKTP.KD.ZG&year=2024").json()
    assert all(country["value"] is None for country in data["countries"])
    assert all(country["observation_year"] == 2024 for country in data["countries"])


def test_map_rejects_unknown_indicators_and_invalid_years(client, populated):
    assert client.get("/api/data/map?indicator=UNKNOWN&year=2024").status_code == 404
    assert (
        client.get("/api/data/map?indicator=NY.GDP.MKTP.KD.ZG&year=1900").status_code
        == 422
    )
