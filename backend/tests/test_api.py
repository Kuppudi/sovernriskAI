import csv
import io

from backend.tests.conftest import ingest_fixture


def test_country_list_search_and_pagination(client, populated):
    page = client.get("/api/countries?limit=1&offset=1").json()
    assert page["total"] == 2 and len(page["items"]) == 1
    assert client.get("/api/countries?search=USA").json()["total"] == 1
    assert client.get("/api/countries/usa").json()["iso3"] == "USA"
    assert client.get("/api/countries?search=%25").json()["total"] == 0


def test_filter_years_indicators_and_missing_data(client, populated):
    response = client.get(
        "/api/countries/USA/indicators?start_year=2024&end_year=2024&indicator=FP.CPI.TOTL.ZG"
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    row = body["items"][0]
    assert row["value"] is None
    assert row["observation_date"] == "2024-01-01"
    assert row["source"] == "World Bank WDI" and row["dataset_version"]
    assert client.get("/api/countries/USA/indicators?indicator=BAD").status_code == 422
    assert (
        client.get(
            "/api/countries/USA/indicators?start_year=2025&end_year=2020"
        ).status_code
        == 422
    )


def test_revised_null_supersedes_old_value_and_old_snapshot_is_queryable(
    client, populated, tmp_path
):
    original = client.get(
        "/api/countries/USA/indicators?indicator=NY.GDP.MKTP.KD.ZG&start_year=2024"
    ).json()["items"][0]
    ingest_fixture(populated, tmp_path, changed=True)
    path = "/api/countries/USA/indicators?indicator=NY.GDP.MKTP.KD.ZG&start_year=2024"
    assert client.get(path).json()["items"][0]["value"] is None
    old = client.get(path + "&dataset_version=" + original["dataset_version"]).json()[
        "items"
    ][0]
    assert old["value"] == 2.5


def test_source_reversion_selects_most_recently_checked_snapshot(
    client, populated, tmp_path
):
    ingest_fixture(populated, tmp_path, changed=True)
    path = "/api/countries/USA/indicators?indicator=NY.GDP.MKTP.KD.ZG&start_year=2024"
    assert client.get(path).json()["items"][0]["value"] is None
    ingest_fixture(populated, tmp_path)
    assert client.get(path).json()["items"][0]["value"] == 2.5


def test_compare_and_validate_scope(client, populated):
    body = {
        "countries": ["USA", "IND"],
        "indicators": ["NY.GDP.MKTP.KD.ZG"],
        "start_year": 2024,
        "end_year": 2024,
    }
    response = client.post("/api/compare", json=body)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2
    assert (
        client.post("/api/compare", json={"countries": ["USA", "USA"]}).status_code
        == 422
    )
    assert (
        client.post("/api/compare", json={"countries": ["USA", "ZZZ"]}).status_code
        == 404
    )


def test_csv_preserves_null_and_zero(client, populated):
    response = client.get("/api/countries/USA/indicators.csv?indicator=FP.CPI.TOTL.ZG")
    assert response.status_code == 200
    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert len(rows) == 2 and all(row["value"] == "" for row in rows)
    response = client.get(
        "/api/countries/USA/indicators.csv?indicator=NY.GDP.MKTP.KD.ZG&end_year=2023"
    )
    assert list(csv.DictReader(io.StringIO(response.text)))[0]["value"] == "0.0"


def test_model_endpoints_never_invent_predictions(client, populated):
    assert client.get("/api/models/status").json()["predictions_available"] == 0
    response = client.get("/api/countries/USA/prediction")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "MODEL_NOT_TRAINED"
    assert (
        client.post(
            "/api/predict", json={"country_iso3": "USA", "as_of_date": "2024-12-31"}
        ).status_code
        == 503
    )
    assert (
        client.post(
            "/api/predict",
            json={
                "country_iso3": "USA",
                "as_of_date": "2024-12-31",
                "features": {"fake": 42},
            },
        ).status_code
        == 422
    )


def test_report_is_deterministic_data_summary(client, populated):
    response = client.get("/api/countries/USA/report")
    assert response.status_code == 200
    report = response.json()
    assert "Synthetic USA" in report["executive_summary"]
    assert len(report["latest_indicators"]) == 5
    assert report["model_status"]["status"] == "unavailable"
    assert report["limitations"]
