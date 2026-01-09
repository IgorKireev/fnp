import asyncio
import random
import time
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

VIN = "LMGAE3G86S1000692"
MAX_ATTEMPTS = 5
GLOBAL_TIMEOUT = 60  # секунд

async def human_behavior(page):
    # движения мыши
    for _ in range(random.randint(3, 6)):
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        await page.mouse.move(x, y, steps=random.randint(5, 15))
        await asyncio.sleep(random.uniform(0.2, 0.6))

    # скролл
    await page.mouse.wheel(0, random.randint(200, 600))
    await asyncio.sleep(random.uniform(0.5, 1.2))


async def main():
    start_time = time.time()
    attempt = 1

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--enable-webgl",
                "--use-gl=desktop",
                "--disable-dev-shm-usage",
            ],
        )

        context = await browser.new_context(
            locale="ru-RU",
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        captcha_failed = False

        async def handle_response(response):
            nonlocal captcha_failed

            if "/api/search/notary" in response.url:
                data = await response.json()
                print(f"\n[ATTEMPT {attempt}] NOTARY:", data)

                if data.get("message") == "Не пройдена проверка CAPTCHA":
                    captcha_failed = True
            if "/api/search/fedresurs" in response.url:
                data = await response.json()
                print(f"\n[ATTEMPT {attempt}] FEDRESURS:", data)

        page.on("response", handle_response)

        await page.goto("https://www.reestr-zalogov.ru/search/index")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        while attempt <= MAX_ATTEMPTS:
            if time.time() - start_time > GLOBAL_TIMEOUT:
                raise TimeoutError("Global timeout reached")

            captcha_failed = False
            print(f"\n▶️ Попытка {attempt}")

            await human_behavior(page)

            await page.get_by_text("По информации о предмете залога").click()
            await asyncio.sleep(random.uniform(0.8, 1.5))

            vin_input = page.locator("#vehicleProperty\\.vin")
            await vin_input.fill("")
            await asyncio.sleep(0.3)
            await vin_input.type(VIN, delay=random.randint(80, 140))

            await asyncio.sleep(random.uniform(0.8, 1.5))
            await page.locator("#find-btn").click()

            await asyncio.sleep(5)

            if not captcha_failed:
                print("✅ CAPTCHA пройдена")
                break

            print("↩ CAPTCHA не пройдена — повтор")
            await page.locator("#back-btn").click()
            await asyncio.sleep(random.uniform(1.5, 2.5))

            attempt += 1

        await browser.close()

asyncio.run(main())
