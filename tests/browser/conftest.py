from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import pytest


@pytest.fixture(scope="session")
def browser_base_url() -> str:
    return os.getenv("KAUCJA_BROWSER_BASE_URL", "http://127.0.0.1:7401")


@pytest.fixture(scope="session")
def browser_artifacts_dir() -> Path:
    path = Path(os.getenv("KAUCJA_BROWSER_ARTIFACTS_DIR", "artifacts/browser"))
    path.mkdir(parents=True, exist_ok=True)
    return path


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
def page(
    browser: Any, browser_artifacts_dir: Path, request: pytest.FixtureRequest
) -> Any:
    test_slug = _slugify(request.node.name)
    test_dir = browser_artifacts_dir / test_slug
    test_dir.mkdir(parents=True, exist_ok=True)

    context = browser.new_context(
        record_video_dir=str(test_dir / "video"),
    )
    context.set_default_timeout(20_000)
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()
    try:
        yield page
    finally:
        failed = bool(
            getattr(request.node, "rep_call", None) and request.node.rep_call.failed
        )
        if failed:
            page.screenshot(
                path=str(test_dir / "failure.png"),
                full_page=True,
            )
            context.tracing.stop(path=str(test_dir / "trace.zip"))
        else:
            context.tracing.stop()
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


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-").lower()
    return normalized or "test"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[Any]) -> Any:
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
