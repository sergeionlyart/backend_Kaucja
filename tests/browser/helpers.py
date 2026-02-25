from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def open_app(page: Any, base_url: str) -> None:
    page.goto(base_url, wait_until="domcontentloaded")
    expect = _expect()
    expect(page.locator("#app_title")).to_be_visible(timeout=20_000)
    expect(page.locator("#analyze_button")).to_be_visible(timeout=20_000)
    expect(page.locator("#history_section")).to_be_visible(timeout=20_000)
    expect(page.locator("#compare_section")).to_be_visible(timeout=20_000)


def click_button(page: Any, elem_id: str) -> None:
    expect = _expect()
    root = page.locator(f"#{elem_id}").first
    expect(root).to_be_visible(timeout=20_000)
    child_button = root.locator("button")
    if child_button.count() > 0:
        child_button.first.click()
        return
    root.click()


def fill_textbox(page: Any, elem_id: str, value: str) -> None:
    expect = _expect()
    textbox = _textbox_locator(page=page, elem_id=elem_id)
    expect(textbox).to_be_visible(timeout=20_000)
    textbox.fill(value)


def textbox_value(page: Any, elem_id: str) -> str:
    expect = _expect()
    textbox = _textbox_locator(page=page, elem_id=elem_id)
    expect(textbox).to_be_visible(timeout=20_000)
    return textbox.input_value()


def expect_textbox_contains(
    page: Any,
    *,
    elem_id: str,
    expected_substring: str,
) -> None:
    expect = _expect()
    textbox = _textbox_locator(page=page, elem_id=elem_id)
    expect(textbox).to_have_value(
        re.compile(re.escape(expected_substring)),
        timeout=20_000,
    )


def set_checkbox(page: Any, elem_id: str, checked: bool) -> None:
    expect = _expect()
    root = page.locator(f"#{elem_id}").first
    checkbox = root.locator("input[type='checkbox']")
    target = checkbox.first if checkbox.count() > 0 else root
    expect(target).to_be_visible(timeout=20_000)
    if checked:
        target.check()
    else:
        target.uncheck()


def upload_file(page: Any, elem_id: str, file_path: Path) -> None:
    expect = _expect()
    root = page.locator(f"#{elem_id}").first
    file_input = root.locator("input[type='file']")
    target = file_input.first if file_input.count() > 0 else root
    expect(target).to_be_attached(timeout=20_000)
    target.set_input_files(str(file_path))


def expect_seeded_runs_visible(page: Any) -> None:
    expect = _expect()
    table = page.locator("#history_runs_table")
    expect(table).to_be_visible(timeout=20_000)
    expect(table.get_by_text("e2e-run-a").first).to_be_visible(timeout=20_000)
    expect(table.get_by_text("e2e-run-b").first).to_be_visible(timeout=20_000)


def _textbox_locator(page: Any, *, elem_id: str) -> Any:
    root = page.locator(f"#{elem_id}").first
    textarea = root.locator("textarea")
    if textarea.count() > 0:
        return textarea.first
    text_input = root.locator("input[type='text']")
    if text_input.count() > 0:
        return text_input.first
    return root


def _expect() -> Any:
    from playwright.sync_api import expect

    return expect
