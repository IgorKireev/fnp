import asyncio
import aiohttp
import time

RUCAPTCHA_API_KEY = "de3461d3d69d631282b52144aa26d1ef"
RUCAPTCHA_CREATE_TASK = "https://api.rucaptcha.com/createTask"
RUCAPTCHA_GET_RESULT = "https://api.rucaptcha.com/getTaskResult"

SITE_KEY = "6LdKJhMaAAAAAIfeHC6FZc-UVfzDQpiOjaJUWoxr"
WEBSITE_URL = "https://www.reestr-zalogov.ru/search/index"
API_URL = "https://www.reestr-zalogov.ru/api/search/notary"


class RuCaptchaError(Exception):
    pass


async def create_recaptcha_v3_task(session, website_url, website_key, page_action, min_score=0.9):
    payload = {
        "clientKey": RUCAPTCHA_API_KEY,
        "task": {
            "type": "RecaptchaV3TaskProxyless",
            "websiteURL": website_url,
            "websiteKey": website_key,
            "pageAction": page_action,
            "minScore": min_score,
            "isEnterprise": False,
        },
    }

    async with session.post(RUCAPTCHA_CREATE_TASK, json=payload) as resp:
        data = await resp.json()

    if data.get("errorId") != 0:
        raise RuCaptchaError(data)

    return data["taskId"]


async def wait_for_result(session, task_id, timeout=120):
    start = time.time()

    while time.time() - start < timeout:
        await asyncio.sleep(3)

        async with session.post(
            RUCAPTCHA_GET_RESULT,
            json={"clientKey": RUCAPTCHA_API_KEY, "taskId": task_id},
        ) as resp:
            result = await resp.json()

        if result.get("status") == "ready":
            return result["solution"]["gRecaptchaResponse"]

        if result.get("errorId") != 0:
            raise RuCaptchaError(result)

    raise TimeoutError("Captcha solving timeout")


async def solve_recaptcha_v3():
    async with aiohttp.ClientSession() as session:
        task_id = await create_recaptcha_v3_task(
            session,
            WEBSITE_URL,
            SITE_KEY,
            page_action="search",
        )
        return await wait_for_result(session, task_id)


async def send_notary_request(token: str):
    headers = {
        "accept": "*/*",
        "content-type": "application/json;charset=UTF-8",
        "origin": "https://www.reestr-zalogov.ru",
        "referer": WEBSITE_URL,
        "x-requested-with": "XMLHttpRequest",
        "user-agent": (
            "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/143.0.0.0 Mobile Safari/537.36"
        ),
    }

    payload = {
        "page": 1,
        "pageSize": 20,
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(
            f"{API_URL}?token={token}",
            json=payload,
        ) as resp:
            print("STATUS:", resp.status)
            data = await resp.json()
            print("RESPONSE JSON:")
            print(data)


async def main():
    token = await solve_recaptcha_v3()
    print("TOKEN RECEIVED:")
    print(token)

    await send_notary_request(token)


if __name__ == "__main__":
    asyncio.run(main())
