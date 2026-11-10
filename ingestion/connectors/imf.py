"""Import selected IMF DataMapper fiscal series, excluding projection years."""

from datetime import date, datetime

from ingestion.connectors.http import SourceError, SourceHTTP
from ingestion.validation.records import ValidatedObservation

BASE_URL = "https://www.imf.org/external/datamapper/api/v2"
PROVIDER = "IMF DataMapper"
LICENSE = "Free public statistical data; attribute IMF and the dataset. Follow IMF statistical-data terms: https://www.imf.org/en/About/copyright-and-terms."

# Provider codes, dataset names, and expected units are deliberately explicit.
SERIES = {
    "GGXWDG_NGDP": ("WEO", "Percent of GDP"),
    "GGXCNL_NGDP": ("WEO", "Percent of GDP"),
    "GGXONLB_G01_GDP_PT": ("FM", "% of GDP"),
    "GGR_G01_GDP_PT": ("FM", "% of GDP"),
}


class ImfClient:
    provider_name = PROVIDER
    license_notes = LICENSE

    def __init__(self, client, base_url=BASE_URL, retries=3):
        self.http = SourceHTTP(client, base_url, retries)
        self.base_url = self.http.base_url
        self.raw_pages = self.http.raw_pages

    async def download(self, countries, start_year, end_year):
        catalog = (await self.http.get("countries")).json().get("countries")
        if not isinstance(catalog, dict) or any(
            code not in catalog for code in countries
        ):
            raise SourceError(
                "IMF country catalog does not contain the requested countries"
            )

        indicators, observations, metadata = [], [], {}
        periods = ",".join(str(year) for year in range(start_year, end_year + 1))
        for code, (dataset, expected_unit) in SERIES.items():
            response = await self.http.get(
                f"{code}/{'/'.join(countries)}", periods=periods
            )
            payload = response.json()
            definition = payload.get("indicators", {}).get(code)
            values = payload.get("values", {}).get(code)
            if not isinstance(definition, dict) or not isinstance(values, dict):
                raise SourceError(f"IMF omitted the definition or values for {code}")
            if (
                definition.get("dataset") != dataset
                or definition.get("unit") != expected_unit
            ):
                raise SourceError(f"IMF changed the dataset or units for {code}")
            cutoff = definition.get("projection-year")
            if type(cutoff) is not int or end_year >= cutoff:
                raise SourceError(
                    f"IMF {code}: choose an end year before its projection year"
                )
            if (
                not definition.get("label")
                or not definition.get("description")
                or not definition.get("source")
            ):
                raise SourceError(f"IMF omitted descriptive metadata for {code}")
            revision = datetime.fromisoformat(definition["last-modified"]).date()
            indicator_code = f"IMF.{dataset}.{code}"
            indicators.append(
                {
                    "code": indicator_code,
                    "name": f"{definition['label']} (IMF)",
                    "category": "Fiscal",
                    "unit": "% of GDP",
                    "definition": definition["description"]
                    + " Historical values may include IMF estimates and revisions; they are not verified point-in-time training data.",
                }
            )
            metadata[indicator_code] = definition
            # Some API responses include extra countries/years despite filters.
            # Select only requested countries and years; never import aggregates.
            for country in countries:
                series = values.get(country, {})
                if not isinstance(series, dict):
                    raise SourceError(f"IMF returned malformed values for {country}")
                for year in range(start_year, end_year + 1):
                    if str(year) not in series:
                        continue  # Absence is a gap, not an invented zero or null.
                    observation = ValidatedObservation(
                        country_iso3=country,
                        indicator_code=indicator_code,
                        observation_date=date(year, 1, 1),
                        value=series[str(year)],
                        source_revision_date=revision,
                    )
                    observations.append(observation.model_dump(mode="json"))
        return {
            "source": self.base_url,
            "start_year": start_year,
            "end_year": end_year,
            "indicators": indicators,
            "observations": observations,
            "provider_metadata": metadata,
        }
