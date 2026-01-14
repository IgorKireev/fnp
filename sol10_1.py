import asyncio
import random
from pathlib import Path
from playwright.async_api import async_playwright

VIN = "LMGAE3G86S1000692"
START_URL = "https://www.reestr-zalogov.ru/search/index"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

PROFILE_DIR = Path("./chrome_profile")

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--enable-webgl",
                "--use-gl=desktop",
                "--ignore-gpu-blocklist",
            ],
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 800},
            locale="ru-RU",
            timezone_id="Europe/Moscow",
        )

        page = await context.new_page()

        # ========= LISTENER =========
        async def handle_response(response):
            try:
                if "/api/search/notary" in response.url:
                    data = await response.json()
                    print("\n[NOTARY RESPONSE]:", data)

                if "/api/search/fedresurs" in response.url:
                    data = await response.json()
                    print("\n[FEDRESURS RESPONSE]:", data)

            except Exception as e:
                print("Response parse error:", e)

        page.on("response", handle_response)

        # ===== STEALTH INIT (оставляем как у тебя) =====
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

        # ===== OPEN PAGE =====
        await page.goto(START_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)

        # ===== ЛЁГКИЙ ПРОГРЕВ =====
        for _ in range(4):
            await page.mouse.move(
                random.randint(200, 1000),
                random.randint(200, 700),
                steps=random.randint(10, 20)
            )
            await page.wait_for_timeout(random.randint(400, 700))

        # ===== SEARCH FLOW =====
        await page.get_by_text("По информации о предмете залога").click()
        await page.wait_for_timeout(1500)

        vin_input = page.locator("#vehicleProperty\\.vin")
        await vin_input.click()

        for ch in VIN:
            await vin_input.type(ch)
            await page.wait_for_timeout(random.randint(90, 160))

        await page.wait_for_timeout(1500)
        await page.locator("#find-btn").click()

        # ⛔ ДАЁМ CAPTCHA ВРЕМЯ
        await page.wait_for_timeout(15000)

        print("\nDONE (browser stays alive)")
        # ❗ НЕ ЗАКРЫВАЕМ CONTEXT — ПУСТЬ ПРОФИЛЬ СОХРАНИТСЯ

if __name__ == "__main__":
    asyncio.run(main())
