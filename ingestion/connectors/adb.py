"""Read annual ADB KIDB liquidity and debt-service data through its SDMX API."""

import re
import xml.etree.ElementTree as ET

from ingestion.connectors.http import SourceError, SourceHTTP
from ingestion.connectors.adb_rows import parse_rows

BASE_URL = "https://kidb.adb.org/api"
PROVIDER = "Asian Development Bank KIDB"
LICENSE = "Public KIDB data; attribute ADB and retain original data sources. Follow https://kidb.adb.org/terms and API rate limits."
SERIES = {
    "RAFA_USD_TOT": "DF_IL",
    "DT_AMT_DLXF_CD": "DF_EXT_DEBT",
    "DT_INT_DLXF_CD": "DF_EXT_DEBT",
}

# ADB's economy codes are not always ISO3. Other codes use their ISO3 spelling.
ECONOMY_CODES = {
    "BGD": "BAN",
    "BTN": "BHU",
    "BRN": "BRU",
    "KHM": "CAM",
    "CHN": "PRC",
    "COK": "COO",
    "FJI": "FIJ",
    "IDN": "INO",
    "MYS": "MAL",
    "MDV": "MLD",
    "MHL": "RMI",
    "MNG": "MON",
    "MMR": "MYA",
    "NRU": "NRO",
    "NPL": "NEP",
    "PHL": "PHI",
    "WSM": "SAM",
    "SGP": "SIN",
    "SLB": "SOL",
    "LKA": "SRI",
    "TWN": "TAP",
    "TJK": "TAJ",
    "TLS": "TIM",
    "VUT": "VAN",
    "VNM": "VIE",
}


def read_country_codes(xml_text):
    root = ET.fromstring(xml_text)
    codes = set()
    for element in root.iter():
        code = element.get("id", "")
        if element.tag.endswith("}Code") and re.fullmatch(r"[A-Z]{3}", code):
            codes.add(code)
    return codes


def make_indicator(code, dataflow, definitions):
    for definition in definitions:
        if definition.get("code") != code:
            continue
        if not definition.get("name"):
            break
        return {
            "code": f"ADB.{dataflow}.{code}",
            "name": f"{definition['name']} (ADB)",
            "category": "External",
            "unit": "million US$",
            "definition": (
                definition.get("description")
                or "ADB has not supplied a detailed definition for this series."
            )
            + " Normalized to millions of US dollars. Original status, reference period, data source, and footnotes are retained in the dataset manifest. Historical values may be estimated or provisional.",
        }
    raise SourceError(f"ADB omitted the definition for {code}")


class AdbClient:
    provider_name = PROVIDER
    license_notes = LICENSE

    def __init__(self, client, base_url=BASE_URL, retries=3, interval=3.1):
        # The official limit is 20 requests/minute. Keep calls sequential.
        self.http = SourceHTTP(client, base_url, retries, interval)
        self.base_url = self.http.base_url
        self.raw_pages = self.http.raw_pages

    async def download(self, countries, start_year, end_year):
        response = await self.http.get(
            "v5/sdmx/structure/codelist/ADB/CL_ECONOMY_CODES/+"
        )
        catalog = read_country_codes(response.text)
        country_codes = {}
        for country in countries:
            provider_code = ECONOMY_CODES.get(country, country)
            if provider_code not in catalog:
                raise SourceError(
                    f"ADB does not cover {country}; choose an ADB economy"
                )
            country_codes[provider_code] = country

        indicators, observations = [], []
        metadata = {"country_codes": country_codes, "definitions": {}, "rows": []}
        for dataflow in sorted(set(SERIES.values())):
            definitions = (
                await self.http.get(f"dataflow/indicators/{dataflow}")
            ).json()
            if not isinstance(definitions, list):
                raise SourceError("ADB indicator catalog is malformed")
            selected_codes = [code for code, flow in SERIES.items() if flow == dataflow]
            for code in selected_codes:
                indicators.append(make_indicator(code, dataflow, definitions))
                metadata["definitions"][code] = next(
                    item for item in definitions if item.get("code") == code
                )
            key = f"A.{'+'.join(selected_codes)}.{'+'.join(country_codes)}"
            response = await self.http.get(
                f"v5/sdmx/data/ADB,{dataflow}/{key}",
                startPeriod=str(start_year),
                endPeriod=str(end_year),
                format="sdmx-csv",
            )
            rows, row_metadata = parse_rows(
                response.text,
                dataflow,
                selected_codes,
                country_codes,
                start_year,
                end_year,
            )
            observations.extend(rows)
            metadata["rows"].extend(row_metadata)
        observations.sort(
            key=lambda row: (
                row["country_iso3"],
                row["indicator_code"],
                row["observation_date"],
            )
        )
        metadata["rows"].sort(
            key=lambda row: (row["country_iso3"], row["indicator_code"], row["year"])
        )
        return {
            "source": self.base_url,
            "start_year": start_year,
            "end_year": end_year,
            "indicators": indicators,
            "observations": observations,
            "provider_metadata": metadata,
        }
