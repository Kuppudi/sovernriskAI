# Importing official data

Run commands from the project root with its Python environment active. `DATABASE_URL` selects the database receiving the rows. A local import does not update Azure unless that URL targets Azure and the network permits the connection.

## World Bank first

World Bank registers country names, regions, and income groups. Register each country before importing it from another provider:

```sh
python -m ingestion.cli --countries USA IND BRA DEU JPN ZAF --start-year 2015 --end-year 2025
```

This command remains unchanged. `--source world-bank` is optional.

## IMF fiscal indicators

```sh
python -m ingestion.cli --source imf --countries USA IND BRA DEU JPN ZAF --start-year 2015 --end-year 2025
```

Four annual series come from the official [IMF DataMapper v2 API](https://www.imf.org/external/datamapper/api/):

| Stored indicator code | Meaning | Dataset |
|---|---|---|
| `IMF.WEO.GGXWDG_NGDP` | General government gross debt / GDP | World Economic Outlook |
| `IMF.WEO.GGXCNL_NGDP` | General government net lending or borrowing / GDP | World Economic Outlook |
| `IMF.FM.GGXONLB_G01_GDP_PT` | General government primary balance / GDP | Fiscal Monitor |
| `IMF.FM.GGR_G01_GDP_PT` | General government revenue / GDP | Fiscal Monitor |

All four use percent of GDP. IMF codes never replace World Bank observations. Provider descriptions, release names, modification dates, and projection cutoffs remain in the raw archive and snapshot manifest. A modification date is not a first-publication date.

Only completed calendar years before every selected series' `projection-year` are allowed. Changed cutoffs, datasets, or units fail validation. Earlier years may contain IMF estimates and revisions. Latest downloaded vintages are not proof of information available at a historical prediction date.

Missing years remain gaps. Explicit nulls remain null; zero stays zero. Every requested country needs at least one numeric observation, while individual indicators may have gaps. Import at most 60 countries per run and run one import at a time. Identical refreshes add audit records without duplicating observations; revisions create new immutable snapshots.

No added API key is needed for this connector. Follow [IMF statistical-data terms](https://www.imf.org/en/About/copyright-and-terms.) and attribute IMF and the named dataset. This project is for noncommercial learning, not LLM training on IMF publications.

## Asian Development Bank

```sh
python -m ingestion.cli --source adb --countries IND JPN --start-year 2015 --end-year 2025
```

ADB covers Asia/Pacific economies, not all countries. Of the initial six imported countries, use India and Japan. An unsupported country fails with an explanation; it is never silently skipped. Register other economies with the World Bank command first. The connector maps ADB's country codes to ISO3 explicitly (for example `PHI` to `PHL`). It excludes subnational areas.

| Stored indicator code | Meaning | Unit |
|---|---|---|
| `ADB.DF_IL.RAFA_USD_TOT` | Total international reserves | million US$ |
| `ADB.DF_EXT_DEBT.DT_AMT_DLXF_CD` | Principal repayments on long-term debt | million US$ |
| `ADB.DF_EXT_DEBT.DT_INT_DLXF_CD` | Interest on long-term debt | million US$ |

The official [KIDB SDMX API](https://kidb.adb.org/api) supplies country/indicator catalogs and CSV data. The connector spaces requests at least 3.1 seconds apart, including retries, to stay under its 20-request/minute limit. Run only one import at a time.

Reported USD multipliers are normalized to millions. Original units, statuses, dataflow version, reference years, footnotes, methodology, and upstream data sources remain in the manifest and raw archive. ADB does not provide detailed descriptions for the two debt series in its catalog; the stored definition discloses that absence. No description is invented.

These are total long-term debt cash flows, not individual loan repayment outcomes. Country/series coverage differs: Japan may have reserves but no external-debt series. Missing years stay absent, explicit missing values stay null, and known forecast or unrecognized observation statuses fail validation. Estimated/provisional history is allowed and identified in source metadata. Annual reference periods can differ across countries. Provider revision dates remain unknown when not supplied.

ADB republishes IMF reserves and World Bank debt data for these series. Keep their provenance, but do not count them as independent evidence or treat correlated series as extra training examples. This small connector prepares data-engineering practice, not a completed global modeling dataset. Follow [KIDB terms](https://kidb.adb.org/terms).

## Azure Quick Deploy

1. Download the GitHub Actions `app-service` artifact, extract its outer archive, and upload the inner `app-service.zip` to Quick Deploy.
2. Enable server-side build. Use Python 3.13 and startup command `bash startup.sh`.
3. After deployment, open a new App Service SSH session. Its existing database URL and VNet connection are reused; no new Azure service or API credential is needed.
4. Run `cd "$APP_PATH"`, then the IMF and ADB commands above. Existing World Bank rows register the six countries. These features do not change the schema or require a new migration.
5. Open Indicators and select an IMF series. Check its Source, compare a country, or export CSV. Models remain unavailable.

App Service imports use `RAW_DATA_DIR=/home/sovereignrisk/raw`. Back up archives with the database. Scheduling, Blob storage, expanded country coverage, ML labels, and training are separate features.
