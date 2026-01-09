import json
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

VIN = "LMGAE3G86S1000692"


def main():
    options = Options()

    # маскировка под обычный Chrome
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    # network/performance logs
    options.set_capability(
        "goog:loggingPrefs",
        {"performance": "ALL"}
    )

    driver = webdriver.Chrome(
        service=Service(),  # chromedriver должен быть в PATH
        options=options
    )

    wait = WebDriverWait(driver, 30)

    print("🌐 Открываем сайт…")
    driver.get("https://www.reestr-zalogov.ru/search/index")

    # даём SPA полностью инициализироваться
    time.sleep(4)

    # === ВКЛАДКА "По информации о предмете залога" ===
    print("🖱️ Кликаем вкладку поиска…")

    tab = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(),'По информации о предмете залога')]")
        )
    )

    # прокрутка + JS-клик (ключевой момент!)
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", tab
    )
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", tab)

    # === VIN ===
    print("⌨️ Ввод VIN…")

    vin_input = wait.until(
        EC.presence_of_element_located((By.ID, "vehicleProperty.vin"))
    )
    vin_input.clear()
    vin_input.send_keys(VIN)

    # === ПОИСК ===
    print("🔍 Нажимаем Поиск…")

    find_btn = wait.until(
        EC.presence_of_element_located((By.ID, "find-btn"))
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", find_btn
    )
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", find_btn)

    print("\n📡 Ждём сетевые ответы (10 сек)…\n")
    time.sleep(10)

    # === NETWORK LOGS ===
    for entry in driver.get_log("performance"):
        try:
            message = json.loads(entry["message"])["message"]
            if message["method"] == "Network.responseReceived":
                url = message["params"]["response"]["url"]
                if "/api/search/notary" in url or "/api/search/fedresurs" in url:
                    print("API RESPONSE URL:", url)
        except Exception:
            pass

    print("\n🧠 Браузер оставлен открытым")
    print("👉 F12 → Network → Fetch/XHR")
    print("👉 Сравни успешный и неуспешный запросы")
    print("👉 Посмотри headers / cookies / timing")

    input("\nНажми Enter, чтобы закрыть браузер…")
    driver.quit()


if __name__ == "__main__":
    main()
