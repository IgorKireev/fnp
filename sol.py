import asyncio
import random
import time
from playwright.async_api import async_playwright
from playwright_stealth import Stealth


VIN = "LMGAE3G86S1000692"

MAX_ATTEMPTS = 5
GLOBAL_TIMEOUT = 90  # секунд

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

START_URL = "https://www.reestr-zalogov.ru/search/index"



async def human_behavior(page):
    # движение мыши
    for _ in range(random.randint(3, 6)):
        x = random.randint(100, 900)
        y = random.randint(100, 700)
        await page.mouse.move(x, y, steps=random.randint(8, 18))
        await asyncio.sleep(random.uniform(0.2, 0.6))

    # скролл
    await page.mouse.wheel(0, random.randint(200, 600))
    await asyncio.sleep(random.uniform(0.6, 1.4))


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
            user_agent=USER_AGENT,
        )

        page = await context.new_page()

        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        # ===== ФЛАГИ СОСТОЯНИЯ =====
        captcha_failed = False
        notary_ok = False
        fedresurs_ok = False

        async def handle_response(response):
            nonlocal captcha_failed, notary_ok, fedresurs_ok

            try:
                if "/api/search/notary" in response.url:
                    data = await response.json()
                    print(f"\n[ATTEMPT {attempt}] NOTARY:", data)

                    if data.get("message") == "Не пройдена проверка CAPTCHA":
                        captcha_failed = True
                        notary_ok = False
                    else:
                        notary_ok = True

                if "/api/search/fedresurs" in response.url:
                    data = await response.json()
                    print(f"\n[ATTEMPT {attempt}] FEDRESURS:", data)

                    if data.get("message") == "Не пройдена проверка CAPTCHA":
                        captcha_failed = True
                        fedresurs_ok = False
                    else:
                        fedresurs_ok = True

            except Exception as e:
                print("Ошибка обработки response:", e)

        page.on("response", handle_response)

        # ===== ОТКРЫВАЕМ СТРАНИЦУ =====
        await page.goto(START_URL)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(random.uniform(1.5, 2.5))

        # ===== ОСНОВНОЙ ЦИКЛ =====
        while attempt <= MAX_ATTEMPTS:
            if time.time() - start_time > GLOBAL_TIMEOUT:
                raise TimeoutError("⏰ Global timeout reached")

            print(f"\n▶️ Попытка {attempt}")

            # сброс флагов
            captcha_failed = False
            notary_ok = False
            fedresurs_ok = False

            await human_behavior(page)

            # выбор поиска
            await page.get_by_text("По информации о предмете залога").click()
            await asyncio.sleep(random.uniform(0.8, 1.4))

            # ввод VIN
            vin_input = page.locator("#vehicleProperty\\.vin")
            await vin_input.fill("")
            await asyncio.sleep(0.4)
            await vin_input.type(VIN, delay=random.randint(80, 140))

            await asyncio.sleep(random.uniform(1.0, 1.6))

            # поиск
            await page.locator("#find-btn").click()

            # ждём backend
            await asyncio.sleep(random.uniform(7.0, 9.0))

            # ===== ПРОВЕРКА РЕЗУЛЬТАТА =====
            if not captcha_failed and notary_ok and fedresurs_ok:
                print("\n✅ NOTARY и FEDRESURS успешно получены")
                break

            print("\n↩ CAPTCHA не пройдена полностью — повтор")

            await page.locator("#back-btn").click()
            await asyncio.sleep(random.uniform(1.8, 2.8))

            attempt += 1

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
