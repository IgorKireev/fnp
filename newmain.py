import asyncio
from playwright.async_api import async_playwright

VIN = "LMGAE3G86S1000692"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        page = await context.new_page()

        async def handle_response(response):
            if "/api/search/notary" in response.url or "/api/search/fedresurs" in response.url:
                try:
                    data = await response.json()
                    print(f"\nRESPONSE from {response.url}:")
                    print(data)
                except Exception as e:
                    print(f"Ошибка при разборе JSON: {e}")

        page.on("response", handle_response)

        # --- 1. Переход на страницу поиска ---
        await page.goto("https://www.reestr-zalogov.ru/search/index")
        await page.wait_for_timeout(1500)

        # --- 2. Клик: "Проверить статус" ---
        await page.get_by_text("Проверить статус").click()
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1500)

        # --- 3. ДОПОЛНИТЕЛЬНЫЙ КЛИК: "Проверить документ" ---
        await page.get_by_text("Проверить документ").click()
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)

        # --- 4. Возврат: "Найти в реестре" ---
        await page.get_by_text("Найти в реестре").click()
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)

        # --- 5. Основной сценарий ---
        await page.get_by_text("По информации о предмете залога").click()

        vin_input = page.locator("#vehicleProperty\\.vin")
        await vin_input.fill(VIN)
        await page.wait_for_timeout(800)

        await page.locator("#find-btn").click()

        await page.wait_for_timeout(15000)
        await browser.close()


asyncio.run(main())
