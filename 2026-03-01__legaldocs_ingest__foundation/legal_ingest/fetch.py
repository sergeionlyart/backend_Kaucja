import httpx
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)
from .config import SourceConfig, HttpConfig
from pydantic import BaseModel
from typing import Dict


class FetchResult(BaseModel):
    raw_bytes: bytes
    status_code: int
    headers: Dict[str, str]
    final_url: str


def _should_retry_error(exc: Exception) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)):
        return True
    return False


def build_client(http_cfg: HttpConfig) -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": http_cfg.user_agent},
        timeout=http_cfg.timeout_seconds,
        follow_redirects=True,
    )


def fetch_direct(client: httpx.Client, url: str) -> FetchResult:
    resp = client.get(url)
    resp.raise_for_status()
    return FetchResult(
        raw_bytes=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers),
        final_url=str(resp.url),
    )


def fetch_saos_judgment(client: httpx.Client, source: SourceConfig) -> FetchResult:
    # Saos API id is extracted from external_ids
    saos_id = source.external_ids.get("saos_id")
    if not saos_id:
        raise ValueError(
            f"SAOS judgment fetch strategy requires external_ids.saos_id on source {source.source_id}"
        )

    api_url = f"https://www.saos.org.pl/api/judgments/{saos_id}"
    resp = client.get(api_url)
    resp.raise_for_status()
    return FetchResult(
        raw_bytes=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers),
        final_url=str(resp.url),
    )


def fetch_source(http_cfg: HttpConfig, source: SourceConfig) -> FetchResult:
    # Wrap in tenacity programmatically so we can use config-based retries
    @retry(
        wait=wait_exponential(multiplier=http_cfg.retry_backoff_seconds),
        stop=stop_after_attempt(http_cfg.max_retries),
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)
        ),
        reraise=True,
    )
    def _do_fetch():
        with build_client(http_cfg) as client:
            if source.fetch_strategy == "direct":
                return fetch_direct(client, str(source.url))
            elif source.fetch_strategy == "saos_judgment":
                return fetch_saos_judgment(client, source)
            elif source.fetch_strategy == "saos_search":
                raise NotImplementedError("SAOS search is delayed to Iteration 3.")
            else:
                raise ValueError(f"Unknown fetch strategy: {source.fetch_strategy}")

    return _do_fetch()
