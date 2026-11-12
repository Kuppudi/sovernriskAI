"""Download official records and turn them into a validated dataset."""

from datetime import date

from ingestion.connectors.world_bank import WorldBankClient
from ingestion.indicators import INDICATORS
from ingestion.validation.records import normalize_iso3, parse_observation


async def download_countries(connector: WorldBankClient, requested: list[str]) -> dict:
    catalog, _ = await connector.fetch("country/all")
    countries = {}

    for row in catalog:
        if row.get("region", {}).get("id") == "NA":
            continue  # Skip regional totals and other World Bank aggregates.

        country_code = normalize_iso3(row["id"])
        if country_code not in requested:
            continue

        countries[country_code] = {
            "iso3": country_code,
            "name": row["name"],
            "region": row["region"]["value"],
            "income_group": row["incomeLevel"]["value"],
        }

    unknown_countries = set(requested) - countries.keys()
    if unknown_countries:
        names = ", ".join(sorted(unknown_countries))
        raise ValueError(f"Unknown or aggregate country codes: {names}")

    return countries


async def download_indicator(connector: WorldBankClient, code: str) -> dict:
    definitions, _ = await connector.fetch(f"indicator/{code}", source="2")
    for definition in definitions:
        if definition.get("id") != code:
            continue
        if not definition.get("name") or not definition.get("sourceNote"):
            break

        return {
            "code": code,
            "name": definition["name"],
            "definition": definition["sourceNote"],
            **INDICATORS[code],
        }

    raise ValueError(f"Missing source definition for {code}")


def get_source_revision(page_metadata: list[dict]) -> date | None:
    revision_dates = {page.get("lastupdated") for page in page_metadata}
    if len(revision_dates) != 1:
        raise ValueError(
            "Source revision changed during pagination; retry the ingestion"
        )

    revision = revision_dates.pop()
    if revision is None:
        return None
    return date.fromisoformat(revision)


async def download_dataset(
    connector: WorldBankClient,
    requested: list[str],
    start_year: int,
    end_year: int,
    *,
    fetch_countries_individually: bool = False,
) -> dict:
    countries = await download_countries(connector, requested)
    indicators = []
    observations = {}
    country_filters = requested if fetch_countries_individually else [";".join(requested)]

    for code in INDICATORS:
        indicators.append(await download_indicator(connector, code))
        rows = []
        page_metadata = []
        for country_filter in country_filters:
            batch_rows, batch_metadata = await connector.fetch(
                f"country/{country_filter}/indicator/{code}",
                date=f"{start_year}:{end_year}",
                source="2",
            )
            rows.extend(batch_rows)
            page_metadata.extend(batch_metadata)
        revision = get_source_revision(page_metadata)

        for row in rows:
            observation = parse_observation(row, code, revision, start_year, end_year)
            if observation.country_iso3 not in countries:
                raise ValueError(
                    "Source returned a country outside the requested scope"
                )

            key = (observation.country_iso3, code, observation.observation_date)
            record = observation.model_dump(mode="json")
            if key in observations and observations[key] != record:
                raise ValueError("Source returned conflicting duplicate observations")
            observations[key] = record

    # Require every requested year, including rows whose value is explicitly null.
    expected_count = len(requested) * len(INDICATORS) * (end_year - start_year + 1)
    if len(observations) != expected_count:
        raise ValueError(
            f"Incomplete source response: expected {expected_count} observations, "
            f"received {len(observations)}"
        )

    return {
        "source": connector.base_url,
        "countries": list(countries.values()),
        "indicators": indicators,
        "start_year": start_year,
        "end_year": end_year,
        "observations": [observations[key] for key in sorted(observations)],
    }
