import aiohttp
import asyncio

RUCAPTCHA_CREATE_TASK = "https://api.rucaptcha.com/createTask"
RUCAPTCHA_GET_RESULT = "https://api.rucaptcha.com/getTaskResult"

RUCAPTCHA_API_KEY = "de3461d3d69d631282b52144aa26d1ef"

SITE_KEY = "6LdKJhMaAAAAAIfeHC6FZc-UVfzDQpiOjaJUWoxr"
SITE_URL = "https://www.reestr-zalogov.ru"
PAGE_ACTION = "search_notary"
MIN_SCORE = 0.9


async def create_captcha_task(session: aiohttp.ClientSession) -> str:
    payload = {
        "clientKey": RUCAPTCHA_API_KEY,
        "task": {
            "type": "RecaptchaV3TaskProxyless",
            "websiteURL": SITE_URL,
            "websiteKey": SITE_KEY,
            "minScore": MIN_SCORE,
            "pageAction": PAGE_ACTION,
            "isEnterprise": False,
        }
    }

    async with session.post(RUCAPTCHA_CREATE_TASK, json=payload) as resp:
        data = await resp.json()

    if data.get("errorId") != 0:
        raise RuntimeError(f"RuCaptcha error: {data}")

    return data["taskId"]

async def wait_captcha_result(session: aiohttp.ClientSession, task_id: str) -> str:
    payload = {
        "clientKey": RUCAPTCHA_API_KEY,
        "taskId": task_id,
    }

    while True:
        await asyncio.sleep(2)

        async with session.post(RUCAPTCHA_GET_RESULT, json=payload) as resp:
            data = await resp.json()

        if data["status"] == "ready":
            print(data)
            return data["solution"]["gRecaptchaResponse"]

        if data.get("errorId", 0) != 0:
            raise RuntimeError(f"RuCaptcha error: {data}")

async def search_notary(session: aiohttp.ClientSession, token: str, vin: str):
    url = f"https://www.reestr-zalogov.ru/api/search/notary?token={token}"

    payload = {
        "mode": "onlyActual",
        "filter": {
            "property": {
                "vehicleProperty": {
                    "vin": vin,
                    "pin": "",
                    "chassis": "",
                    "bodyNum": ""
                }
            }
        },
        "limit": 10,
        "offset": 0
    }

    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.reestr-zalogov.ru/search/index",
        "Origin": "https://www.reestr-zalogov.ru",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/143.0.0.0 Safari/537.36"
        )
    }

    async with session.post(url, json=payload, headers=headers) as resp:
        return await resp.json()


async def main():
    vin = "LMGAE3G86S1000692"

    async with aiohttp.ClientSession() as session:
        task_id = await create_captcha_task(session)
        print("Task ID:", task_id)

        token = await wait_captcha_result(session, task_id)
        print("Captcha token received")

        result = await search_notary(session, token, vin)
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
