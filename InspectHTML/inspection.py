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

def open_categories_mercadona(postal_code):
    driver = load_chrome_webdriver(headless=False)
    driver.get("https://tienda.mercadona.es/categories")

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
    
    return driver


from bs4 import BeautifulSoup

def press_each_product_cell(driver):
    try:
        product_cells = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-container .product-cell--actionable"))
        )
        i = 0
        for cell in product_cells:
            i += 1
            cell.click()
            print("Product cell clicked.")
            time.sleep(3)  # Adjust sleep time as necessary
            
            # Save the page source
            pageSource = driver.page_source
            # with open(f"mercadona_product_{i}.html", "w", encoding="utf-8") as file:
            #     file.write(pageSource)
            
            # Parse the page source with BeautifulSoup
            soup = BeautifulSoup(pageSource, 'html.parser')
            
            # Extract product details
            title = soup.select_one('.private-product-detail__description').get_text(strip=True)
            format_size = ' '.join([span.get_text(strip=True) for span in soup.select('.product-format__size .headline1-r')])
            previous_price = soup.select_one('.product-price__previous-unit-price').get_text(strip=True)
            current_price = soup.select_one('.product-price__unit-price--discount').get_text(strip=True)
            units = soup.select_one('.product-price__extra-price').get_text(strip=True)
            allergens = soup.select_one('.private-product-detail__left').get('aria-label')
            
            # Print extracted details
            print(f"Title: {title}")
            print(f"Format Size: {format_size}")
            print(f"Previous Price: {previous_price}{units}")
            print(f"Current Price: {current_price}{units}")
            print(f"Allergens and other info: {allergens}")
            
            # Find the last product-gallery__thumbnail element and print its link
            thumbnails = driver.find_elements(By.CSS_SELECTOR, ".product-gallery__thumbnail img")
            if thumbnails:
                url_img = thumbnails[-1]
                url_img = url_img.get_attribute("src")
                url_img = url_img.replace("h=300", "h=1600").replace("w=300", "w=1600") #Change the resolution to be able to read it.
                print(f"Last thumbnail link: {url_img}")

            # Navigate back to the categories page
            driver.back()
            time.sleep(3)  # Adjust sleep time as necessary to ensure the page loads
            
    except Exception as e:
        print(f"Error clicking product cells: {e}")
            
    except Exception as e:
        print(f"Error clicking product cells: {e}")

if __name__ == "__main__":
    postal_code = "23009"
    driver = open_categories_mercadona(postal_code)
    time.sleep(3)
    press_each_product_cell(driver)
    # pageSource = driver.page_source
    # with open("mercadona_categories.html", "w", encoding="utf-8") as file:
    #     file.write(pageSource)
    driver.close()
        