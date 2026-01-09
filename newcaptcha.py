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
            )
        )

        page = await context.new_page()

        async def handle_response(response):
            global captcha_failed

            if "/api/search/notary" in response.url:
                data = await response.json()
                print(f"\n[ATTEMPT {attempt}] NOTARY:", data)

                if data.get("message") == "Не пройдена проверка CAPTCHA":
                    captcha_failed = True

            if "/api/search/fedresurs" in response.url:
                data = await response.json()
                print(f"\n[ATTEMPT {attempt}] FEDRESURS:", data)

        page.on("response", handle_response)

        # === ШАГ 1: открываем страницу ===
        await page.goto("https://www.reestr-zalogov.ru/search/index")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)  

        # === ШАГ 2: функция поиска ===
        async def do_search():
            await page.get_by_text("По информации о предмете залога").click()
            await asyncio.sleep(1)

            vin_input = page.locator("#vehicleProperty\\.vin")
            await vin_input.fill("")
            await asyncio.sleep(0.5)
            await vin_input.fill(VIN)

            await asyncio.sleep(1)
            await page.locator("#find-btn").click()

        # === ПЕРВАЯ ПОПЫТКА ===
        print("\n▶️ Первая попытка поиска")
        await do_search()
        await asyncio.sleep(5)

        # === ЕСЛИ CAPTCHA → ВОЗВРАТ И ПОВТОР ===
        if captcha_failed:
            attempt = 2
            captcha_failed = False

            print("\n↩ CAPTCHA detected — возвращаемся и повторяем поиск")

            await page.locator("#back-btn").click()
            await asyncio.sleep(2)

            await do_search()
            await asyncio.sleep(5)

        print("\n✅ Сценарий завершён, смотри ответы API")
        await asyncio.sleep(10)
        await browser.close()


asyncio.run(main())
