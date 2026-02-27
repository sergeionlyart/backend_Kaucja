import asyncio
from playwright.async_api import async_playwright

async def get_screenshot():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            await page.goto("http://127.0.0.1:7861", timeout=15000)
        except Exception:
            pass
        await page.screenshot(path="artifacts/antigravity/quote/20260227_094133/P0_01/screenshot.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_screenshot())
