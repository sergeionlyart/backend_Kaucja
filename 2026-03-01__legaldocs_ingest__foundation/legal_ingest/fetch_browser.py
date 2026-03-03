"""Browser-based fetcher using Playwright for WAF-protected sites.

Used as fallback when direct httpx fetch fails with WAF challenge or
malformed headers. Returns the same FetchResult contract as fetch.py.
"""
import logging
from typing import Optional

from .fetch import FetchResult

logger = logging.getLogger(__name__)

# Lazy-loaded playwright to avoid import cost when not needed
_browser_instance = None
_playwright_instance = None


def _get_browser():
    """Lazy-init Playwright browser (reusable across calls)."""
    global _browser_instance, _playwright_instance
    if _browser_instance is None:
        from playwright.sync_api import sync_playwright
        _playwright_instance = sync_playwright().start()
        _browser_instance = _playwright_instance.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        logger.info("Playwright Chromium browser launched")
    return _browser_instance


def close_browser():
    """Shutdown Playwright browser + instance."""
    global _browser_instance, _playwright_instance
    if _browser_instance:
        _browser_instance.close()
        _browser_instance = None
    if _playwright_instance:
        _playwright_instance.stop()
        _playwright_instance = None


def fetch_with_browser(
    url: str,
    timeout_ms: int = 30_000,
    wait_for_selector: Optional[str] = None,
) -> FetchResult:
    """Fetch URL using headless Chromium browser.

    Args:
        url: The URL to fetch.
        timeout_ms: Page load timeout in milliseconds.
        wait_for_selector: Optional CSS selector to wait for before capturing content.

    Returns:
        FetchResult with rendered HTML content.
    """
    browser = _get_browser()
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 800},
        java_script_enabled=True,
    )

    page = context.new_page()

    try:
        response = page.goto(url, timeout=timeout_ms, wait_until="networkidle")

        if response is None:
            raise ValueError(f"Playwright got null response for {url}")

        status_code = response.status

        # Wait for content to render
        if wait_for_selector:
            page.wait_for_selector(wait_for_selector, timeout=timeout_ms)
        else:
            # Default: wait a bit for JS to settle
            page.wait_for_timeout(2000)

        # Get the rendered HTML
        html_content = page.content()
        raw_bytes = html_content.encode("utf-8")

        # Get final URL after redirects
        final_url = page.url

        # Build headers dict from response
        headers = dict(response.headers) if response.headers else {}
        headers["content-type"] = "text/html; charset=utf-8"  # always HTML from browser

        logger.info(
            "Browser fetch succeeded for %s (%d bytes, status %d)",
            url, len(raw_bytes), status_code,
        )

        return FetchResult(
            raw_bytes=raw_bytes,
            status_code=status_code,
            headers=headers,
            final_url=final_url,
        )
    finally:
        context.close()
