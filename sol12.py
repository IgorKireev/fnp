import asyncio
import random
from playwright.async_api import async_playwright

VIN = "LMGAE3G86S1000692"
START_URL = "https://www.reestr-zalogov.ru/search/index"

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/141.0.0.0 Safari/537.36"
)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--enable-webgl",
                "--use-gl=desktop",
            ],
        )

        context = await browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1366, "height": 768},
            locale="ru-RU",
            timezone_id="Europe/Moscow",
        )

        page = await context.new_page()

        # ===== RESPONSE LISTENER =====
        async def handle_response(response):
            try:
                if "/api/search/notary" in response.url:
                    print("\n[NOTARY]:", await response.json())
                if "/api/search/fedresurs" in response.url:
                    print("\n[FEDRESURS]:", await response.json())
            except:
                pass

        page.on("response", handle_response)

        # ===== STEALTH INIT =====
        await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => false });

        Object.defineProperty(navigator, 'platform', {
            get: () => 'Linux x86_64'
        });

        Object.defineProperty(navigator, 'languages', {
            get: () => ['ru-RU', 'ru']
        });

        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8
        });

        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8
        });

        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                { name: 'Chrome PDF Plugin' },
                { name: 'Chrome PDF Viewer' },
                { name: 'Native Client' }
            ]
        });

        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) =>
            parameters.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : originalQuery(parameters);

        window.chrome = { runtime: {} };

        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) return 'Intel Open Source Technology Center';
            if (parameter === 37446) return 'Mesa DRI Intel(R) UHD Graphics';
            return getParameter.call(this, parameter);
        };
        """)

        # ===== PAGE LOAD =====
        await page.goto(START_URL, wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # ===== HUMAN SCROLL =====
        for _ in range(3):
            await page.mouse.wheel(0, random.randint(200, 400))
            await page.wait_for_timeout(random.randint(400, 700))

        # ===== TAB CLICK =====
        await page.get_by_text("По информации о предмете залога").click()
        await page.wait_for_timeout(1500)

        # ===== VIN INPUT =====
        vin_input = page.locator("#vehicleProperty\\.vin")
        await vin_input.click()
        for ch in VIN:
            await vin_input.type(ch)
            await page.wait_for_timeout(random.randint(90, 160))

        # ===== WAIT reCAPTCHA COOKIE =====
        for _ in range(10):
            cookies = await context.cookies()
            if any(c["name"] == "_GRECAPTCHA" for c in cookies):
                break
            await page.wait_for_timeout(500)

        # ===== SUBMIT =====
        await page.locator("#find-btn").click()

        await page.wait_for_timeout(15000)

        print("\nDONE")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
