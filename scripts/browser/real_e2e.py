import argparse
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright


def run_real_e2e(
    provider_name: str, file_path: str, base_url: str, timeout_seconds: int
) -> dict[str, object]:
    start_time = time.time()
    result = {
        "provider": provider_name,
        "status": "failed",
        "error_message": "UNKNOWN_ERROR",
        "run_id": None,
        "latency_seconds": 0.0,
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(base_url)

            # Wait for app load
            page.locator("#analyze_button").wait_for()

            # Select provider if not default
            if provider_name.lower() != "openai":
                page.get_by_label("Provider").first.click()
                page.get_by_role("option", name="Google").click()
                time.sleep(1)
                page.get_by_label("Model").first.click()
                page.get_by_role("option", name="gemini-2.5-flash").first.click()
                time.sleep(1)

            # Upload Document
            file_input = page.locator("input[type='file']").first
            file_input.set_input_files(file_path)
            time.sleep(1)

            page.locator("#analyze_button").click()

            for _ in range(timeout_seconds):
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

            browser.close()

            result["status"] = (
                "completed" if "completed" in final_status.lower() else "failed"
            )
            result["run_id"] = run_id if run_id else None
            result["error_message"] = error_msg if error_msg else None

    except Exception as e:
        result["error_message"] = str(e)

    result["latency_seconds"] = round(time.time() - start_time, 2)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Real E2E via Playwright on a specific document."
    )
    parser.add_argument("--base-url", required=True, help="Base URL of Gradio app")
    parser.add_argument(
        "--file-path", required=True, help="Absolute path to the document to test"
    )
    parser.add_argument(
        "--providers",
        required=True,
        help="Comma separated providers (e.g. openai,google)",
    )
    parser.add_argument(
        "--timeout-seconds", type=int, default=120, help="Max wait time for generation"
    )
    parser.add_argument(
        "--output-report",
        required=True,
        help="Path to write the deterministic JSON report",
    )
    args = parser.parse_args()

    providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    report = {"overall_status": "pass", "providers": []}

    for provider in providers:
        res = run_real_e2e(
            provider_name=provider,
            file_path=args.file_path,
            base_url=args.base_url,
            timeout_seconds=args.timeout_seconds,
        )
        report["providers"].append(res)
        if res["status"] != "completed":
            report["overall_status"] = "fail"

    out_path = Path(args.output_report)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))

    print(f"E2E generated `{report['overall_status']}` for {providers}")


if __name__ == "__main__":
    main()
