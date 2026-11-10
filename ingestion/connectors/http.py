"""Small HTTP helper for official data sources; each source parses its own format."""

import asyncio
import logging
import time

import httpx

logger = logging.getLogger("sovereign.ingestion")


class SourceError(RuntimeError):
    pass


class SourceHTTP:
    def __init__(self, client, base_url, retries=3, interval=0):
        self.client = client
        self.base_url = base_url.rstrip("/")
        self.retries = retries
        self.interval = interval
        self.last_request = 0.0
        self.raw_pages = []

    async def get(self, path, **params):
        for attempt in range(self.retries + 1):
            # ADB's limit applies to retries as well as successful requests.
            delay = self.interval - (time.monotonic() - self.last_request)
            if delay > 0:
                await asyncio.sleep(delay)
            self.last_request = time.monotonic()
            try:
                response = await self.client.get(
                    f"{self.base_url}/{path.lstrip('/')}", params=params, timeout=45
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                status = error.response.status_code
                if status != 429 and status < 500:
                    raise SourceError(f"Source returned HTTP {status}") from error
            except httpx.TransportError:
                pass
            else:
                self.raw_pages.append(
                    {"url": str(response.request.url), "response": response.text}
                )
                return response
            if attempt < self.retries:
                logger.warning(
                    "source_retry source=%s attempt=%s", self.base_url, attempt + 1
                )
                await asyncio.sleep(min(2**attempt, 8))
        raise SourceError("Source request failed after retries")
