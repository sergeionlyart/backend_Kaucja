from __future__ import annotations

import os
import time
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import pytest


@pytest.fixture(scope="session")
def browser_base_url() -> str:
    return os.getenv("KAUCJA_BROWSER_BASE_URL", "http://127.0.0.1:7861")


@pytest.fixture(scope="session", autouse=True)
def _browser_test_gate(browser_base_url: str) -> None:
    if os.getenv("KAUCJA_RUN_BROWSER_TESTS", "0") != "1":
        pytest.skip(
            "Browser tests are disabled. Set KAUCJA_RUN_BROWSER_TESTS=1 to run.",
            allow_module_level=True,
        )
    _wait_for_url(browser_base_url, timeout_seconds=45.0)


@pytest.fixture(scope="session")
def _playwright() -> Any:
    playwright_api = pytest.importorskip("playwright.sync_api")
    with playwright_api.sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(_playwright: Any) -> Any:
    browser = _playwright.chromium.launch(headless=True)
    try:
        yield browser
    finally:
        browser.close()


@pytest.fixture()
def page(browser: Any) -> Any:
    context = browser.new_context()
    page = context.new_page()
    try:
        yield page
    finally:
        context.close()


def _wait_for_url(url: str, *, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: str | None = None

    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=3) as response:
                status = getattr(response, "status", 200)
                if 200 <= int(status) < 500:
                    return
        except URLError as error:
            last_error = str(error)
        except TimeoutError as error:
            last_error = str(error)

        time.sleep(0.5)

    message = (
        f"Gradio app did not become available: {url}. "
        f"Last error: {last_error or 'unknown'}"
    )
    raise RuntimeError(message)
