"""Paginated World Bank V2 connector. No synthetic fallback or silent failures."""

import asyncio
import logging
from typing import Any

import httpx

from ingestion.connectors.http import SourceError

logger = logging.getLogger("sovereign.ingestion")


class WorldBankClient:
    def __init__(
        self,
        client: httpx.AsyncClient,
        base_url: str = "https://api.worldbank.org/v2",
        retries: int = 3,
    ):
        self.client = client
        self.base_url = base_url.rstrip("/")
        self.retries = retries
        self.raw_pages: list[dict[str, Any]] = []

    async def fetch(self, path: str, **params: str) -> tuple[list[dict], list[dict]]:
        records: list[dict] = []
        metadata: list[dict] = []
        page = 1
        while True:
            payload = await self._request(
                path,
                {**params, "format": "json", "per_page": "1000", "page": str(page)},
            )
            if (
                not isinstance(payload, list)
                or len(payload) != 2
                or not isinstance(payload[0], dict)
            ):
                raise SourceError(
                    "World Bank returned an error or malformed response envelope"
                )
            meta, rows = payload
            try:
                pages = int(meta["pages"])
                returned_page = int(meta["page"])
            except (KeyError, TypeError, ValueError) as exc:
                raise SourceError("World Bank pagination metadata is invalid") from exc
            if returned_page != page or pages < 1 or pages > 10000:
                raise SourceError("World Bank pagination is out of bounds")
            if rows is None:
                if int(meta.get("total", -1)) != 0:
                    raise SourceError(
                        "World Bank omitted records despite a nonempty result"
                    )
                rows = []
            if not isinstance(rows, list) or any(
                not isinstance(row, dict) for row in rows
            ):
                raise SourceError("World Bank records must be objects")
            self.raw_pages.append(
                {
                    "path": path,
                    "params": dict(params, page=str(page)),
                    "response": payload,
                }
            )
            records.extend(rows)
            metadata.append(meta)
            if page >= pages:
                break
            page += 1
        return records, metadata

    async def _request(self, path: str, params: dict) -> Any:
        for attempt in range(self.retries + 1):
            try:
                response = await self.client.get(
                    f"{self.base_url}/{path.lstrip('/')}", params=params, timeout=30
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code != 429 and exc.response.status_code < 500:
                    raise SourceError(
                        f"World Bank HTTP {exc.response.status_code}"
                    ) from exc
            except (httpx.TransportError, ValueError):
                pass
            if attempt < self.retries:
                logger.warning("source_retry path=%s attempt=%s", path, attempt + 1)
                await asyncio.sleep(min(2**attempt, 8))
        raise SourceError(
            f"World Bank request failed after {self.retries + 1} attempts: {path}"
        )
