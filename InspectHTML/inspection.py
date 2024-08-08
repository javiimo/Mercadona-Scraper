from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time


def load_chrome_webdriver(headless=False):
    options = Options()
    options.add_argument("user-data-dir=C:/Users/javym/AppData/Local/Google/Chrome/User Data")  # User path to avoid having to choose a default browser
    options.add_argument("--headless") if headless else None
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver



if __name__ == "__main__":
    driver = load_chrome_webdriver(headless=False)
    driver.get("https://tienda.mercadona.es/categories")
    time.sleep(4)
    pageSource = driver.page_source
    with open("mercadona_categories.html", "w", encoding="utf-8") as file:
        file.write(pageSource)
    driver.close()
        