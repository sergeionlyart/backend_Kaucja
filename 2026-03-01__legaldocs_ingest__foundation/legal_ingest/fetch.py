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
import logging
from urllib.parse import urlparse, quote

logger = logging.getLogger(__name__)


SAOS_MAINTENANCE_SIGNATURES = [
    b"Przerwa techniczna",
    b"przerwa techniczna",
    b"maintenance",
]

EURLEX_DOMAINS = ("eur-lex.europa.eu",)


class SaosMaintenanceError(Exception):
    """Raised when SAOS returns a maintenance/technical-break page."""
    def __init__(self, source_id: str, bytes_len: int):
        self.source_id = source_id
        self.bytes_len = bytes_len
        super().__init__(
            f"SAOS maintenance page detected for {source_id} ({bytes_len} bytes). "
            "Both API and HTML endpoints return 'Przerwa techniczna' page."
        )


class EurlexWafChallengeError(Exception):
    """Raised when EUR-Lex returns an AWS WAF challenge (0 bytes, HTTP 200)."""
    def __init__(self, url: str, status_code: int, content_len: int):
        self.url = url
        self.status_code = status_code
        self.content_len = content_len
        super().__init__(
            f"EURLEX_WAF_CHALLENGE: EUR-Lex returned HTTP {status_code} with "
            f"{content_len} bytes (AWS WAF challenge page). URL: {url}"
        )


def is_saos_maintenance(content: bytes) -> bool:
    """Check if content is a SAOS maintenance/technical-break page."""
    if len(content) > 5000:
        return False
    return any(sig in content for sig in SAOS_MAINTENANCE_SIGNATURES)


def is_eurlex_waf_challenge(url: str, status_code: int, content: bytes) -> bool:
    """Detect EUR-Lex AWS WAF challenge: HTTP 200/202/403 with 0 bytes."""
    if not any(d in url for d in EURLEX_DOMAINS):
        return False
    if len(content) == 0 and status_code in (200, 202, 403):
        return True
    # Also detect very small WAF challenge HTML pages
    if len(content) < 500 and status_code in (200, 202, 403):
        if b"awswaf" in content.lower() or b"captcha" in content.lower():
            return True
    return False


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

    # EUR-Lex WAF challenge detection
    if is_eurlex_waf_challenge(final_url, resp.status_code, raw_bytes):
        raise EurlexWafChallengeError(
            url=final_url,
            status_code=resp.status_code,
            content_len=len(raw_bytes),
        )

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
            pass  # fallback to original bytes if parsing fails

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

        # Check JSON response isn't empty/maintenance
        if is_saos_maintenance(resp.content):
            raise ValueError("SAOS API returned maintenance page in JSON wrapper")

        return FetchResult(
            raw_bytes=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers),
            final_url=str(resp.url),
        )
    except (ValueError, httpx.HTTPStatusError):
        # Fallback to HTML
        html_url = f"https://www.saos.org.pl/judgments/{saos_id}"
        resp_html = client.get(html_url)
        resp_html.raise_for_status()

        # Check if HTML fallback is also a maintenance page
        if is_saos_maintenance(resp_html.content):
            logger.warning(
                "SAOS maintenance detected on both API and HTML for %s",
                source.source_id,
            )
            raise SaosMaintenanceError(
                source_id=source.source_id,
                bytes_len=len(resp_html.content),
            )

        return FetchResult(
            raw_bytes=resp_html.content,
            status_code=resp_html.status_code,
            headers=dict(resp_html.headers),
            final_url=str(resp_html.url),
        )


# --- Transport ladder types ---

def _make_attempt(
    source_id: str,
    attempt_no: int,
    method: str,
    status_code: int | None,
    nbytes: int | None,
    reason_code: str,
    duration_ms: int,
    final_outcome: str,
) -> dict:
    """Build a fetch attempt record for fetch_attempts.jsonl."""
    return {
        "source_id": source_id,
        "attempt_no": attempt_no,
        "method": method,
        "status_code": status_code,
        "bytes": nbytes,
        "reason_code": reason_code,
        "duration_ms": duration_ms,
        "final_outcome": final_outcome,
    }


# Errors that trigger browser fallback
BROWSER_FALLBACK_ERRORS = (EurlexWafChallengeError,)

# Check at runtime if httpcore is available for RemoteProtocolError
try:
    import httpcore
    BROWSER_FALLBACK_ERRORS = (
        EurlexWafChallengeError,
        httpcore.RemoteProtocolError,
        httpx.RemoteProtocolError,
    )
except ImportError:
    # Fallback: at least include httpx-level errors
    BROWSER_FALLBACK_ERRORS = (
        EurlexWafChallengeError,
        httpx.RemoteProtocolError,
    )


def fetch_source(
    http_cfg: HttpConfig,
    source: SourceConfig,
    browser_fallback_config=None,
    browser_fallback_counter: list | None = None,
) -> tuple[FetchResult, list[dict]]:
    """Fetch a source using transport ladder: direct_httpx -> browser_playwright.

    Browser fallback is policy-driven:
    - Only triggers on BROWSER_FALLBACK_ERRORS
    - Only for domains in browser_fallback_config.allowed_domains
    - Respects circuit breaker (max_browser_fallbacks_per_run)
    - Graceful BROWSER_RUNTIME_MISSING if Playwright not installed

    Args:
        http_cfg: HTTP configuration.
        source: Source to fetch.
        browser_fallback_config: Browser fallback policy configuration.
        browser_fallback_counter: Mutable list used as counter [current_count].

    Returns:
        Tuple of (FetchResult, attempt_log).
    """
    import time as _time
    from .reason_codes import ReasonCode

    attempt_log: list[dict] = []

    # --- Attempt 1: direct httpx with tenacity retries ---
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

    t0 = _time.time()
    try:
        result = _do_fetch()
        dur = int((_time.time() - t0) * 1000)
        attempt_log.append(_make_attempt(
            source_id=source.source_id,
            attempt_no=1,
            method="direct_httpx",
            status_code=result.status_code,
            nbytes=len(result.raw_bytes),
            reason_code=ReasonCode.OK,
            duration_ms=dur,
            final_outcome="OK",
        ))
        return result, attempt_log
    except BROWSER_FALLBACK_ERRORS as e:
        dur = int((_time.time() - t0) * 1000)
        reason = ReasonCode.classify_error(str(e))
        fallback_outcome = "FALLBACK_TO_BROWSER"

        # --- Policy check: should we attempt browser fallback? ---
        skip_browser = False
        skip_reason = ""

        if browser_fallback_config is None or not browser_fallback_config.enabled:
            skip_browser = True
            skip_reason = "browser_fallback disabled in config"
            fallback_outcome = "ERROR"

        if not skip_browser:
            url_str = str(source.url)
            domain_allowed = any(
                d in url_str for d in browser_fallback_config.allowed_domains
            )
            if not domain_allowed:
                skip_browser = True
                skip_reason = f"domain not in allowed_domains: {browser_fallback_config.allowed_domains}"
                fallback_outcome = "ERROR"

        if not skip_browser and browser_fallback_counter is not None:
            if browser_fallback_counter[0] >= browser_fallback_config.max_browser_fallbacks_per_run:
                skip_browser = True
                skip_reason = f"circuit breaker: max_browser_fallbacks ({browser_fallback_config.max_browser_fallbacks_per_run}) reached"
                fallback_outcome = "ERROR"

        attempt_log.append(_make_attempt(
            source_id=source.source_id,
            attempt_no=1,
            method="direct_httpx",
            status_code=getattr(e, "status_code", None),
            nbytes=getattr(e, "content_len", 0),
            reason_code=reason,
            duration_ms=dur,
            final_outcome=fallback_outcome,
        ))

        if skip_browser:
            logger.warning(
                "Direct fetch failed (%s), browser fallback skipped: %s for %s",
                reason, skip_reason, source.source_id,
            )
            e.attempt_log = attempt_log  # type: ignore[attr-defined]
            raise

        logger.warning(
            "Direct fetch failed (%s), falling back to browser for %s",
            reason, source.source_id,
        )
    except Exception as e:
        dur = int((_time.time() - t0) * 1000)
        reason = ReasonCode.classify_error(str(e))
        attempt_log.append(_make_attempt(
            source_id=source.source_id,
            attempt_no=1,
            method="direct_httpx",
            status_code=None,
            nbytes=None,
            reason_code=reason,
            duration_ms=dur,
            final_outcome="ERROR",
        ))
        # Attach attempt_log to exception so pipeline can always capture telemetry
        e.attempt_log = attempt_log  # type: ignore[attr-defined]
        raise

    # --- Attempt 2: browser (Playwright) ---
    if browser_fallback_counter is not None:
        browser_fallback_counter[0] += 1

    timeout_ms = 30_000
    if browser_fallback_config:
        timeout_ms = browser_fallback_config.browser_timeout_ms

    t1 = _time.time()
    try:
        from .fetch_browser import fetch_with_browser
        result = fetch_with_browser(str(source.url), timeout_ms=timeout_ms)
        dur2 = int((_time.time() - t1) * 1000)
        attempt_log.append(_make_attempt(
            source_id=source.source_id,
            attempt_no=2,
            method="browser_playwright",
            status_code=result.status_code,
            nbytes=len(result.raw_bytes),
            reason_code=ReasonCode.OK,
            duration_ms=dur2,
            final_outcome="OK",
        ))
        return result, attempt_log
    except ImportError:
        dur2 = int((_time.time() - t1) * 1000)
        attempt_log.append(_make_attempt(
            source_id=source.source_id,
            attempt_no=2,
            method="browser_playwright",
            status_code=None,
            nbytes=None,
            reason_code="BROWSER_RUNTIME_MISSING",
            duration_ms=dur2,
            final_outcome="ERROR",
        ))
        logger.error(
            "Browser runtime not available (playwright not installed) for %s",
            source.source_id,
        )
        err = EurlexWafChallengeError(
            url=str(source.url), status_code=0, content_len=0,
        )
        err.attempt_log = attempt_log  # type: ignore[attr-defined]
        raise err
    except Exception as e2:
        dur2 = int((_time.time() - t1) * 1000)
        reason2 = ReasonCode.classify_error(str(e2))
        attempt_log.append(_make_attempt(
            source_id=source.source_id,
            attempt_no=2,
            method="browser_playwright",
            status_code=None,
            nbytes=None,
            reason_code=reason2,
            duration_ms=dur2,
            final_outcome="ERROR",
        ))
        err2 = EurlexWafChallengeError(
            url=str(source.url), status_code=0, content_len=0,
        )
        err2.attempt_log = attempt_log  # type: ignore[attr-defined]
        raise err2 from e2


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
