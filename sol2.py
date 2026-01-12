import asyncio
import random
import time
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# ================== CONFIG ==================

VIN = "LMGAE3G86S1000692"

START_URL = "https://www.reestr-zalogov.ru/search/index"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

MAX_ATTEMPTS = 7
GLOBAL_TIMEOUT = 120  # seconds

# ============================================


async def human_behavior(page):
    # мелкие движения мыши
    for _ in range(random.randint(4, 7)):
        x = random.randint(150, 1000)
        y = random.randint(150, 700)
        await page.mouse.move(x, y, steps=random.randint(10, 25))
        await page.wait_for_timeout(random.randint(200, 600))

    # несколько скроллов
    for _ in range(random.randint(2, 4)):
        await page.mouse.wheel(0, random.randint(200, 500))
        await page.wait_for_timeout(random.randint(500, 1200))


async def mouse_click_center(page, locator):
    box = await locator.bounding_box()
    if not box:
        raise RuntimeError("Element not visible for mouse click")

    x = box["x"] + box["width"] / 2
    y = box["y"] + box["height"] / 2

    await page.mouse.move(x, y, steps=random.randint(8, 15))
    await page.wait_for_timeout(random.randint(200, 400))
    await page.mouse.down()
    await page.wait_for_timeout(random.randint(50, 120))
    await page.mouse.up()


async def type_like_human(locator, text):
    await locator.fill("")
    await asyncio.sleep(random.uniform(0.3, 0.6))
    for ch in text:
        await locator.type(ch)
        await asyncio.sleep(random.uniform(0.08, 0.15))


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
            user_agent=USER_AGENT,
            locale="ru-RU",
            viewport={"width": 1280, "height": 800},
        )

        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        # ===== FLAGS =====
        notary_ok = False
        fedresurs_ok = False
        captcha_failed = False

        async def handle_response(response):
            nonlocal notary_ok, fedresurs_ok, captcha_failed

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
                print("Response parse error:", e)

        page.on("response", handle_response)

        # ===== OPEN PAGE =====
        await page.goto(START_URL)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(random.randint(2000, 3000))

        # ===== MAIN LOOP =====
        while attempt <= MAX_ATTEMPTS:
            if time.time() - start_time > GLOBAL_TIMEOUT:
                raise TimeoutError("Global timeout reached")

            print(f"\n▶️ ATTEMPT {attempt}")

            notary_ok = False
            fedresurs_ok = False
            captcha_failed = False

            await human_behavior(page)

            # выбрать тип поиска
            await mouse_click_center(
                page,
                page.get_by_text("По информации о предмете залога"),
            )
            await page.wait_for_timeout(random.randint(800, 1400))

            # VIN
            vin_input = page.locator("#vehicleProperty\\.vin")
            await mouse_click_center(page, vin_input)
            await type_like_human(vin_input, VIN)

            await page.wait_for_timeout(random.randint(1200, 1800))

            # кнопка поиска
            await mouse_click_center(page, page.locator("#find-btn"))

            # КРИТИЧЕСКИ ВАЖНО: дать v3 время
            await page.wait_for_timeout(random.randint(10000, 14000))

            if not captcha_failed and notary_ok and fedresurs_ok:
                print("\n✅ SUCCESS: NOTARY + FEDRESURS OK")
                break

            print("\n↩ CAPTCHA FAILED → retry")

            await mouse_click_center(page, page.locator("#back-btn"))
            await page.wait_for_timeout(random.randint(2000, 3000))

            attempt += 1

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
