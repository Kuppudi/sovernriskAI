# Data dictionary

Names/definitions come from the provider; curated mappings live in `ingestion/indicators.py`.

| Code | Meaning | Unit |
|---|---|---|
| `NY.GDP.MKTP.KD.ZG` | GDP growth | annual % |
| `NY.GDP.PCAP.CD` | GDP per capita | current US$ per person |
| `FP.CPI.TOTL.ZG` | Consumer inflation | annual % |
| `NE.EXP.GNFS.ZS` | Exports of goods and services | % of GDP |
| `NE.IMP.GNFS.ZS` | Imports of goods and services | % of GDP |
| `BN.CAB.XOKA.GD.ZS` | Current account balance | % of GDP |

Provider: [World Bank Indicators API V2](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation), WDI source `2`. Exclude aggregates (`region.id = NA`). ISO3 codes must also exist in the provider's non-aggregate country catalog; only requested countries are stored. Country classifications are provider metadata.

- `countries`: ISO3, name, region, income group.
- `indicators`: unique provider code, name/definition, curated category/unit, source FK.
- `observations`: country/indicator FKs, annual period as `YYYY-01-01`, nullable finite value, nullable first-publication date, nullable response revision date, UTC first retrieval, dataset FK. Unique by country/indicator/year/version; indexed by series/year.
- `data_sources`: provider, API URL, license caveat, last successful check.
- `ingestion_runs`: UUID, source, start/end, status, validated row count including nulls, sanitized error, snapshot FK on success. Identical refreshes create audit runs without duplicate observations.
- `data_snapshots`: SHA-256 identity, first creation, source FK, original JSON path, scope/indicator manifest. Raw archive includes fetched pages and normalized country/indicator/observation metadata.
- `rating_events`: empty until authorized data exists; agency, country, instrument/issuer scope, currency basis, effective date, prior/new rating, event type. Unique by scope/date.
- `model_versions`: reserved model name/version, trained date, artifact URI, metrics, feature schema. A row does not authorize serving.
- `predictions`: reserved country/as-of/model/snapshot references, nullable outputs, generated time. Probability is constrained to [0,1]. No fabricated rows.

`retrieved_at` and `latest_successful_refresh` describe collection. Revision date does not establish first publication or individual-observation revision. `observation_count` includes retained vintages and missing rows, not just latest usable values. Default queries choose the most recently checked snapshot per series/year; `dataset_version` retrieves a specific snapshot.

Reject non-finite values, booleans, numeric strings, unexpected countries/indicators/years, conflicting duplicates, incomplete responses, and provider error envelopes. Nulls are never imputed. Back up raw files with the database. Review dataset-specific licensing and third-party restrictions before redistribution.

The map endpoint returns one selected indicator and exact observation year per imported country, using the latest successfully checked version. A missing row and a reported null both stay uncolored; `observation_year` distinguishes an absent row from an explicit missing observation. Country shape geometry is a separate locally bundled Natural Earth dataset, documented in `frontend/public/maps/README.md`; its presence does not imply economic data coverage.
