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
                raise ValueError("saos_search should be expanded prior to fetch_source")
            else:
                raise ValueError(f"Unknown fetch strategy: {source.fetch_strategy}")

    return _do_fetch()


def expand_saos_search(
    http_cfg: HttpConfig, source: SourceConfig
) -> list[SourceConfig]:
    base_url = "https://www.saos.org.pl/api/search/judgments"
    params = dict(source.saos_search_params or {})
    params.setdefault("pageSize", 100)
    page_num = 0

    seen_ids = set()
    new_sources = []

    with build_client(http_cfg) as client:
        while True:
            params["pageNumber"] = page_num
            resp = client.get(base_url, params=params)
            resp.raise_for_status()
            data = resp.json()

            items = data.get("items", [])
            for item in items:
                saos_id = str(item.get("id"))
                if saos_id and saos_id not in seen_ids:
                    seen_ids.add(saos_id)
                    ext_ids = dict(source.external_ids or {})
                    ext_ids["saos_id"] = saos_id

                    ns = SourceConfig(
                        source_id=f"{source.source_id}_{saos_id}",
                        url="https://www.saos.org.pl",
                        fetch_strategy="saos_judgment",
                        doc_type_hint="CASELAW",
                        jurisdiction=source.jurisdiction,
                        language=source.language,
                        external_ids=ext_ids,
                        license_tag=source.license_tag,
                    )
                    new_sources.append(ns)

            links = data.get("links", [])
            has_next = any(link.get("rel") == "next" for link in links)
            if not items or not has_next:
                break
            page_num += 1

    return new_sources
