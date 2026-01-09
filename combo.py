import asyncio
from playwright.async_api import async_playwright

VIN = "LMGAE3G86S1000692"
captcha_failed = False
attempt = 1

async def main():
    global captcha_failed, attempt

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        page = await context.new_page()

        # --- ловим API ответы ---
        async def handle_response(response):
            global captcha_failed

            if "/api/search/notary" in response.url:
                try:
                    data = await response.json()
                    print(f"\n[ATTEMPT {attempt}] NOTARY:", data)
                    if data.get("message") == "Не пройдена проверка CAPTCHA":
                        captcha_failed = True
                except Exception as e:
                    print(f"Ошибка JSON: {e}")

            if "/api/search/fedresurs" in response.url:
                try:
                    data = await response.json()
                    print(f"\n[ATTEMPT {attempt}] FEDRESURS:", data)
                except Exception as e:
                    print(f"Ошибка JSON: {e}")

        page.on("response", handle_response)

        # --- 1. Переход на страницу поиска ---
        await page.goto("https://www.reestr-zalogov.ru/search/index")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1.5)

        # --- 2. "Проверить статус" ---
        await page.get_by_text("Проверить статус", exact=True).click()
        await asyncio.sleep(1.5)

        # --- 3. "Проверить документ" ---
        await page.get_by_text("Проверить документ", exact=True).click()
        await asyncio.sleep(2)

        # --- 4. "Найти в реестре" ---
        await page.get_by_text("Найти в реестре", exact=True).click()
        await asyncio.sleep(2)

        # --- функция поиска VIN ---
        async def do_search():
            await page.get_by_text("По информации о предмете залога", exact=True).click()
            await asyncio.sleep(0.5)

            vin_input = page.locator("#vehicleProperty\\.vin")
            await vin_input.wait_for(state="visible")
            await vin_input.fill("")  # очистка поля
            await asyncio.sleep(0.5)
            await vin_input.fill(VIN)

            await asyncio.sleep(0.5)
            await page.locator("#find-btn").click()

        # --- первая попытка ---
        print("\n▶️ Первая попытка поиска")
        await do_search()
        await asyncio.sleep(5)

        # --- если CAPTCHA → возвращаемся и повторяем ---
        if captcha_failed:
            attempt = 2
            captcha_failed = False
            print("↩ CAPTCHA detected — возвращаемся и повторяем поиск")

            back_btn = page.locator("#back-btn")
            await back_btn.wait_for(state="visible", timeout=10000)
            await back_btn.click()
            await asyncio.sleep(2)

            await do_search()
            await asyncio.sleep(5)

        print("\n✅ Сценарий завершён, смотри ответы API")
        await asyncio.sleep(5)
        await browser.close()


asyncio.run(main())
