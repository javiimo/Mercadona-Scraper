from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time


def load_chrome_webdriver(headless=False):
    options = Options()
    options.add_argument("user-data-dir=C:/Users/javym/AppData/Local/Google/Chrome/User Data")  # User path to avoid having to choose a default browser
    options.add_argument("--incognito")  # Open in incognito mode to avoid saving cookies and cache
    options.add_argument("--disable-extensions")  # Disable extensions
    options.add_argument("--headless") if headless else None
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver



if __name__ == "__main__":
    postal_code = "23009"
    driver = load_chrome_webdriver(headless=False)
    driver.get("https://tienda.mercadona.es/categories")
    #time.sleep(4)

    # Handle cookies by pressing "Rechazar"
    try:
        rechazar_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Rechazar')]"))
        )
        rechazar_button.click()
        print("Cookies rejected successfully.")
    except Exception as e:
        print("Did not show up cookies or could not find the reject button.")


    # Postal Code
    try:
        # Input the postal code
        postal_code_input = driver.find_element(By.CSS_SELECTOR, "input[data-testid='postal-code-checker-input']")
        postal_code_input.send_keys(postal_code)

        # Press continuar
        continuar_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='postal-code-checker-button']")
        continuar_button.click()
        print("Postal code selected successfully.")
    except Exception:
        print("Did not ask for postal code")

    time.sleep(4)
    pageSource = driver.page_source
    with open("mercadona_categories.html", "w", encoding="utf-8") as file:
        file.write(pageSource)
    driver.close()
        