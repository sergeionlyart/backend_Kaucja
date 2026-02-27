import time
from playwright.sync_api import sync_playwright


def run_real_e2e(provider_name: str):
    file_path = "/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/fixtures/1/Faktura PGE.pdf"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://127.0.0.1:7861")

        # Wait for app load
        page.locator("#analyze_button").wait_for()

        # Select provider if not default
        if provider_name.lower() != "openai":
            page.get_by_label("Provider").first.click()
            page.get_by_role("option", name="Google").click()
            time.sleep(1)

        # Upload Document
        file_input = page.locator("input[type='file']").first
        file_input.set_input_files(file_path)
        print(f"[{provider_name}] Uploaded {file_path}")
        time.sleep(1)

        print(f"[{provider_name}] Clicking Analyze...")
        page.locator("#analyze_button").click()

        for i in range(120):  # Up to 120 seconds for processing
            status_locator = page.locator("#run_status_box textarea")
            if status_locator.count() > 0:
                status = status_locator.input_value()
                if (
                    "completed" in status.lower()
                    or "failed" in status.lower()
                    or "error" in status.lower()
                    or "aborted" in status.lower()
                ):
                    break

            error_locator = page.locator("#run_error_box textarea")
            if error_locator.count() > 0:
                err = error_locator.input_value()
                if err and len(err.strip()) > 0:
                    break

            time.sleep(1)

        final_status = page.locator("#run_status_box textarea").input_value()
        error_msg = page.locator("#run_error_box textarea").input_value()
        run_id = page.locator("#run_id_box textarea").input_value()

        print(f"[{provider_name}] --- RESULT ---")
        print(f"Status: {final_status}")
        print(f"Error: {error_msg}")
        print(f"Run ID: {run_id}")

        browser.close()


if __name__ == "__main__":
    print("Executing OpenAI...")
    run_real_e2e("OpenAI")
    print("\nExecuting Google...")
    run_real_e2e("Google Gemini")
