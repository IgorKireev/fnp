import asyncio
from playwright.async_api import async_playwright

VIN = "LMGAE3G86S1000692"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            slow_mo=50,
        )

        context = await browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"),
        )

        page = await context.new_page()

        async def handle_response(response):
            if "/api/search/notary" in response.url or "/api/search/fedresurs" in response.url:
                try:
                    data = await response.json()
                    print(f"RESPONSE from {response.url}:")
                    print(data)
                except Exception as e:
                    print(f"Ошибка при разборе JSON: {e}")

        page.on("response", handle_response)

        await page.goto("https://www.reestr-zalogov.ru/search/index")

        await page.get_by_text("По информации о предмете залога").click()

        vin_input = page.locator("#vehicleProperty\\.vin")
        await vin_input.fill(VIN)

        await page.locator("#find-btn").click()

        await page.wait_for_timeout(15000)

        await browser.close()

asyncio.run(main())
