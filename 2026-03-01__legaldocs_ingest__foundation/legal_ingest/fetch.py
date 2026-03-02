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
import re
from urllib.parse import urlparse, quote


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
    cookies = {}
    if http_cfg.lex_session_cookie:
        # Standard approach for LEX systems
        cookies["JSESSIONID"] = http_cfg.lex_session_cookie

    return httpx.Client(
        headers={"User-Agent": http_cfg.user_agent},
        cookies=cookies,
        timeout=http_cfg.timeout_seconds,
        follow_redirects=True,
    )


def transform_lex_url(url: str) -> str:
    # Match id from /dzu-dziennik-ustaw/...-{documentId}
    # and optional unit id like /art-19-a
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    parts = path.split("/")
    
    doc_id = None
    unit_id_raw = None
    
    for pt in parts:
        if pt.startswith("art-"):
            unit_id_raw = pt
        elif "-" in pt and pt[-1].isdigit():
            # Lex document URLs usually end with a long numeric ID like -16903658
            # Path-123 should be ignored unless it maps generically
            match = re.search(r'-(\d{7,10})$', pt)
            if match:
                doc_id = match.group(1)

    if not doc_id:
        return url
        
    base_endpoint = f"https://sip.lex.pl/apimobile/document/{doc_id}?documentConfigurationId=lawJournal"
    
    if unit_id_raw:
        # art-19-a -> art(19(a))
        # Remove 'art-' prefix
        u_suffix = unit_id_raw[4:]
        sub_parts = u_suffix.split("-")
        
        # Build nested parenthesis: 19, a -> 19(a)
        if len(sub_parts) == 1:
            unit_id = f"art({sub_parts[0]})"
        else:
            # Simple assumption for 2 parts like 19-a
            unit_id = f"art({sub_parts[0]}({sub_parts[1]}))"
        
        base_endpoint += f"&unitId={quote(unit_id)}"
        
    return base_endpoint


def fetch_direct(client: httpx.Client, url: str) -> FetchResult:
    is_lex = "sip.lex.pl" in url
    fetch_url = transform_lex_url(url) if is_lex else url
    
    resp = client.get(fetch_url)
    resp.raise_for_status()
    
    raw_bytes = resp.content
    final_url = str(resp.url)
    
    if is_lex and resp.headers.get("content-type", "").startswith("application/json"):
        try:
            data = resp.json()
            # Try to grab HTML content
            if "content" in data:
                raw_bytes = data["content"].encode("utf-8")
                # Mutate headers so pipeline considers this HTML
                new_headers = dict(resp.headers)
                new_headers["content-type"] = "text/html; charset=utf-8"
                return FetchResult(
                    raw_bytes=raw_bytes,
                    status_code=resp.status_code,
                    headers=new_headers,
                    final_url=final_url,
                )
        except Exception:
            pass # fallback to original bytes if parsing fails
            
    return FetchResult(
        raw_bytes=raw_bytes,
        status_code=resp.status_code,
        headers=dict(resp.headers),
        final_url=final_url,
    )


def fetch_saos_judgment(client: httpx.Client, source: SourceConfig) -> FetchResult:
    # Saos API id is extracted from external_ids
    saos_id = source.external_ids.get("saos_id")
    if not saos_id:
        raise ValueError(
            f"SAOS judgment fetch strategy requires external_ids.saos_id on source {source.source_id}"
        )

    api_url = f"https://www.saos.org.pl/api/judgments/{saos_id}"
    try:
        resp = client.get(api_url)
        resp.raise_for_status()
        
        # Verify it's actually JSON and not a maintenance HTML page
        if "application/json" not in resp.headers.get("content-type", "").lower():
            raise ValueError("SAOS API returned non-JSON response")
            
        return FetchResult(
            raw_bytes=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers),
            final_url=str(resp.url),
        )
    except ValueError:
        # Fallback to HTML
        html_url = f"https://www.saos.org.pl/judgments/{saos_id}"
        resp_html = client.get(html_url)
        resp_html.raise_for_status()
        return FetchResult(
            raw_bytes=resp_html.content,
            status_code=resp_html.status_code,
            headers=dict(resp_html.headers),
            final_url=str(resp_html.url),
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
    
    @retry(
        wait=wait_exponential(multiplier=http_cfg.retry_backoff_seconds),
        stop=stop_after_attempt(http_cfg.max_retries),
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)
        ),
        reraise=True,
    )
    def _do_expand():
        base_url = "https://www.saos.org.pl/api/search/judgments"
        params = dict(source.saos_search_params or {})
        params.setdefault("pageSize", 100)
        page_num = 0

        seen_ids = set()
        new_sources = []

        with build_client(http_cfg) as client:
            try:
                while True:
                    params["pageNumber"] = page_num
                    resp = client.get(base_url, params=params)
                    resp.raise_for_status()
                    
                    if "application/json" not in resp.headers.get("content-type", "").lower():
                        raise ValueError("SAOS search API returned non-JSON")
                    
                    data = resp.json()

                    items = data.get("items", [])
                    for item in items:
                        raw_id = item.get("id")
                        if raw_id is None or raw_id == "":
                            continue
                        saos_id = str(raw_id)
                        if saos_id not in seen_ids:
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
                    
            except ValueError:
                # Fallback to HTML search page crawling
                from bs4 import BeautifulSoup
                
                # map API params to HTML params if needed (usually similar)
                html_search_url = "https://www.saos.org.pl/search"
                # HTML pagination uses 'page' (1-indexed usually, though saos handles ?page= param)
                # Assuming params passed from source.saos_search_params work for HTML query as well
                # e.g. {"courtCriteria.courtType": "COMMON", "keywords": "kaucja mieszkaniowa"}
                
                html_params = dict(source.saos_search_params or {})
                
                # Start from page=1 for HTML fallback
                current_page = 1
                while True:
                    html_params["page"] = current_page
                    resp_html = client.get(html_search_url, params=html_params)
                    resp_html.raise_for_status()
                    
                    soup = BeautifulSoup(resp_html.content, "html.parser")
                    judgments_found_on_page = False
                    
                    # Find all links to /judgments/{id}
                    for a_tag in soup.find_all("a", href=True):
                        href = a_tag["href"]
                        if href.startswith("/judgments/") or href.startswith("https://www.saos.org.pl/judgments/"):
                            # extract ID
                            match = re.search(r'/judgments/(\d+)', href)
                            if match:
                                judgments_found_on_page = True
                                saos_id = match.group(1)
                                if saos_id not in seen_ids:
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
                                    
                    # Check pagination for 'Next' or just if we found items
                    # The UI usually has <a rel="next"> or similar depending on SAOS markup.
                    # A safe heuristic: if no judgments were found, we reached the end.
                    if not judgments_found_on_page:
                        break
                        
                    current_page += 1

        return new_sources
        
    return _do_expand()
