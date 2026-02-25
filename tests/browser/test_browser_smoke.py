from __future__ import annotations

from pathlib import Path
from typing import Any

from tests.browser.helpers import (
    click_button,
    expect_seeded_runs_visible,
    expect_textbox_contains,
    fill_textbox,
    open_app,
    set_checkbox,
    textbox_value,
    upload_file,
)


def test_p0_app_starts_and_core_sections_render(
    page: Any, browser_base_url: str
) -> None:
    open_app(page=page, base_url=browser_base_url)


def test_p0_history_loads_seeded_run_and_outputs_render(
    page: Any, browser_base_url: str
) -> None:
    open_app(page=page, base_url=browser_base_url)

    click_button(page, "history_refresh_button")
    expect_seeded_runs_visible(page)

    fill_textbox(page, "history_run_id_input", "e2e-run-a")
    click_button(page, "history_load_button")

    expect_textbox_contains(
        page,
        elem_id="run_status_box",
        expected_substring="History loaded.",
    )
    expect_textbox_contains(
        page,
        elem_id="summary_box",
        expected_substring="critical_gaps_summary",
    )
    expect_textbox_contains(
        page,
        elem_id="raw_json_box",
        expected_substring='"checklist"',
    )
    expect_textbox_contains(
        page,
        elem_id="validation_box",
        expected_substring="Validation:",
    )


def test_p0_compare_seeded_runs_returns_diff_and_metrics(
    page: Any, browser_base_url: str
) -> None:
    open_app(page=page, base_url=browser_base_url)

    click_button(page, "history_refresh_button")
    expect_seeded_runs_visible(page)
    click_button(page, "compare_button")

    expect_textbox_contains(
        page,
        elem_id="compare_status_box",
        expected_substring="Comparison ready.",
    )
    expect_textbox_contains(
        page,
        elem_id="compare_json_box",
        expected_substring="checklist_diff",
    )
    expect_textbox_contains(
        page,
        elem_id="compare_metrics_box",
        expected_substring="delta (B - A)",
    )


def test_p0_export_run_bundle_from_history(page: Any, browser_base_url: str) -> None:
    open_app(page=page, base_url=browser_base_url)

    click_button(page, "history_refresh_button")
    expect_seeded_runs_visible(page)
    fill_textbox(page, "history_run_id_input", "e2e-run-a")
    click_button(page, "history_export_button")

    expect_textbox_contains(
        page,
        elem_id="export_status_box",
        expected_substring="Export completed.",
    )
    zip_path = textbox_value(page, "export_path_box")
    assert zip_path.endswith("_bundle.zip")
    assert Path(zip_path).is_file()


def test_p0_restore_verify_only_for_exported_zip(
    page: Any, browser_base_url: str
) -> None:
    open_app(page=page, base_url=browser_base_url)

    click_button(page, "history_refresh_button")
    expect_seeded_runs_visible(page)
    fill_textbox(page, "history_run_id_input", "e2e-run-a")
    click_button(page, "history_export_button")
    expect_textbox_contains(
        page,
        elem_id="export_status_box",
        expected_substring="Export completed.",
    )
    zip_path = Path(textbox_value(page, "export_path_box"))
    assert zip_path.is_file()

    upload_file(page, "restore_zip_file_input", zip_path)
    set_checkbox(page, "restore_verify_only_checkbox", True)
    click_button(page, "restore_button")

    expect_textbox_contains(
        page,
        elem_id="restore_status_box",
        expected_substring="Verification completed.",
    )
    expect_textbox_contains(
        page,
        elem_id="restore_details_box",
        expected_substring="manifest_verification=",
    )
    expect_textbox_contains(
        page,
        elem_id="restore_details_box",
        expected_substring="verify_only=True",
    )
