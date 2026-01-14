import asyncio
import random
import time
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

VIN = "LMGAE3G86S1000692"
START_URL = "https://www.reestr-zalogov.ru/search/index"

# Реальный UA под Windows + Chrome Stable
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

async def human_behavior(page):
    for _ in range(random.randint(3, 6)):
        await page.mouse.move(
            random.randint(100, 1200),
            random.randint(100, 700),
            steps=random.randint(10, 25)
        )
        await asyncio.sleep(random.uniform(0.2, 0.5))

    await page.mouse.wheel(0, random.randint(300, 700))
    await asyncio.sleep(random.uniform(0.5, 1.2))


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="chrome",
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-dev-shm-usage",
            ],
        )

        context = await browser.new_context(
            user_agent=USER_AGENT,
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            viewport={"width": 1280, "height": 800},
            color_scheme="light",
        )

        page = await context.new_page()

        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        # ===== ЛОГИРУЕМ API =====
        async def handle_response(response):
            if "/api/search/notary" in response.url:
                print("\n[NOTARY]:", await response.json())
            if "/api/search/fedresurs" in response.url:
                print("\n[FEDRESURS]:", await response.json())

        page.on("response", handle_response)

        # ===== СТАРТ =====
        await page.goto(START_URL, wait_until="networkidle")
        await asyncio.sleep(random.uniform(1.5, 2.5))

        await human_behavior(page)

        # Выбор режима поиска
        await page.get_by_text("По информации о предмете залога").click()
        await asyncio.sleep(random.uniform(0.8, 1.4))

        # Ввод VIN
        vin_input = page.locator("#vehicleProperty\\.vin")
        await vin_input.click()
        await asyncio.sleep(0.3)
        await vin_input.fill("")
        await vin_input.type(VIN, delay=random.randint(80, 140))

        await asyncio.sleep(random.uniform(1.0, 1.6))

        # Поиск
        await page.locator("#find-btn").click()

        # Ждём backend
        await asyncio.sleep(10)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
