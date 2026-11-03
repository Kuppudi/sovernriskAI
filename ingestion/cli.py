"""Run: python -m ingestion.cli --countries USA IND BRA --start-year 2015 --end-year 2025"""

import argparse
import asyncio
from datetime import date

import httpx
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging
from backend.app.db.session import get_engine
from ingestion.connectors.world_bank import WorldBankClient
from ingestion.pipelines.world_bank import ingest_world_bank


async def run(args) -> None:
    settings = get_settings()
    async with httpx.AsyncClient(
        headers={"User-Agent": "SovereignRiskPlatform/0.1 (economic research)"}
    ) as client:
        with Session(get_engine()) as db:
            result = await ingest_world_bank(
                db,
                WorldBankClient(client, settings.world_bank_base_url),
                args.countries,
                args.start_year,
                args.end_year,
                settings.raw_data_dir,
            )
            print(
                f"Completed {result.id}: {result.records_processed} observations; dataset {result.dataset_version}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest official World Bank WDI observations, without fabricated values"
    )
    parser.add_argument(
        "--countries", nargs="+", default=["USA", "IND", "BRA", "DEU", "JPN", "ZAF"]
    )
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=date.today().year - 1)
    configure_logging()
    args = parser.parse_args()
    try:
        asyncio.run(run(args))
    except Exception as exc:
        # Do not print database URLs or library tracebacks containing secrets.
        parser.exit(
            1,
            f"Ingestion failed ({type(exc).__name__}). Check source availability, database migrations, and requested country/year scope.\n",
        )


if __name__ == "__main__":
    main()
