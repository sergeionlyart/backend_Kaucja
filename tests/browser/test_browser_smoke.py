from __future__ import annotations

import time
from typing import Any


def test_browser_app_renders_core_sections(page: Any, browser_base_url: str) -> None:
    page.goto(browser_base_url, wait_until="domcontentloaded")

    page.get_by_role("heading", name="Kaucja Case Sandbox").wait_for(state="visible")
    page.get_by_role("button", name="Analyze").wait_for(state="visible")
    page.get_by_text("Prompt Management").wait_for(state="visible")
    page.get_by_text("Run History").wait_for(state="visible")
    page.get_by_text("Compare Runs").wait_for(state="visible")


def test_browser_history_load_and_compare_flow(
    page: Any, browser_base_url: str
) -> None:
    page.goto(browser_base_url, wait_until="domcontentloaded")

    page.get_by_role("button", name="Refresh History").click()
    page.get_by_text("e2e-run-b").first.wait_for(state="visible")
    page.get_by_role("button", name="Compare Selected Runs").click()
    _wait_for_textbox_contains(
        page=page,
        label="Compare Status",
        expected_substring="Comparison ready.",
    )

    page.get_by_label("Run ID to load").fill("e2e-run-b")
    page.get_by_role("button", name="Load Selected Run").click()
    _wait_for_textbox_contains(
        page=page,
        label="Status",
        expected_substring="History loaded.",
    )

    summary_value = page.get_by_label(
        "Summary (critical gaps + next questions)"
    ).input_value()
    assert "critical_gaps_summary" in summary_value


def _wait_for_textbox_contains(
    *,
    page: Any,
    label: str,
    expected_substring: str,
    timeout_seconds: float = 20.0,
) -> None:
    textbox = page.get_by_role("textbox", name=label, exact=True)
    deadline = time.monotonic() + timeout_seconds
    last_value = ""

    while time.monotonic() < deadline:
        last_value = textbox.input_value()
        if expected_substring in last_value:
            return
        time.sleep(0.2)

    raise AssertionError(
        (
            f"Textbox '{label}' did not contain '{expected_substring}' "
            f"within {timeout_seconds:.1f}s. Last value: {last_value!r}"
        )
    )
