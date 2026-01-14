import asyncio
import random
from playwright.async_api import async_playwright

VIN = "LMGAE3G86S1000692"
START_URL = "https://www.reestr-zalogov.ru/search/index"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

MAX_RETRIES = 3


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--enable-webgl",
                "--use-gl=desktop",
                "--ignore-gpu-blocklist",
            ],
        )

        context = await browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 800},
            locale="ru-RU",
            timezone_id="Europe/Moscow",
        )

        page = await context.new_page()

        # ===== FLAGS =====
        notary_ok = False
        fedresurs_ok = False
        captcha_failed = False

        # ===== RESPONSE LISTENER =====
        async def handle_response(response):
            nonlocal notary_ok, fedresurs_ok, captcha_failed

            try:
                if "/api/search/notary" in response.url:
                    data = await response.json()
                    print("\n[NOTARY RESPONSE]:", data)

                    if data.get("message") == "Не пройдена проверка CAPTCHA":
                        captcha_failed = True
                        notary_ok = False
                    else:
                        notary_ok = True

                if "/api/search/fedresurs" in response.url:
                    data = await response.json()
                    print("\n[FEDRESURS RESPONSE]:", data)

                    if data.get("message") == "Не пройдена проверка CAPTCHA":
                        captcha_failed = True
                        fedresurs_ok = False
                    else:
                        fedresurs_ok = True

            except Exception as e:
                print("Response parse error:", e)

        page.on("response", handle_response)

        # ===== STEALTH =====
        await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => false });

        Object.defineProperty(navigator, 'languages', {
            get: () => ['ru-RU', 'ru']
        });

        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8
        });

        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8
        });

        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) return 'Intel Inc.';
            if (parameter === 37446) return 'Intel Iris OpenGL Engine';
            return getParameter.call(this, parameter);
        };
        """)

        await page.goto(START_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        retries = 0

        while retries < MAX_RETRIES:
            print(f"\n▶️ TRY {retries + 1}")

            notary_ok = False
            fedresurs_ok = False
            captcha_failed = False

            # минимальная "человечность" — как у тебя
            for _ in range(3):
                await page.mouse.move(
                    random.randint(200, 1000),
                    random.randint(200, 700),
                    steps=15
                )
                await page.wait_for_timeout(400)

            await page.get_by_text("По информации о предмете залога").click()
            await page.wait_for_timeout(1200)

            vin_input = page.locator("#vehicleProperty\\.vin")
            await vin_input.click()

            for ch in VIN:
                await vin_input.type(ch)
                await page.wait_for_timeout(random.randint(80, 150))

            await page.wait_for_timeout(1200)
            await page.locator("#find-btn").click()

            # ⛔ важно дать reCAPTCHA v3 время оценить поведение
            await page.wait_for_timeout(12000)

            if not captcha_failed and notary_ok and fedresurs_ok:
                print("\n✅ SUCCESS")
                break

            print("\n↩ RETRY (captcha or partial fail)")
            retries += 1

            await page.locator("#back-btn").click()
            await page.wait_for_timeout(2500)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
