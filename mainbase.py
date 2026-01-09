import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            # slow_mo=50  # замедляет ВСЕ действия
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        page = await context.new_page()
        await page.goto("https://www.reestr-zalogov.ru/search/index")

        print("Браузер открыт. Вводи всё вручную.")
        await asyncio.sleep(600)  # 10 минут

asyncio.run(main())
