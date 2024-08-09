from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
import csv
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




def press_each_product_cell(driver, categorie, subcategorie):
    try:

        # Check if the file exists and is not empty
        file_exists = os.path.isfile('mercadona.csv') and os.path.getsize('products_info.csv') > 0

        with open('mercadona.csv', mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter='$') #! Notice the $ separator to make sure it is not contained in the description of the product
            
            # Write the header ro   w only if the file is empty
            if not file_exists:
                writer.writerow(['categorie', 'subcategorie', 'product name', 'format size', 'previous price', 'current price', 'units', 'description', 'link'])

            
            product_cells = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-container .product-cell--actionable"))
                        )
            for cell in product_cells:
                cell.click()
                print("Product cell clicked.")
                time.sleep(3)  # Adjust sleep time as necessary
                
                # Save the page source
                pageSource = driver.page_source
                
                # Parse the page source with BeautifulSoup
                soup = BeautifulSoup(pageSource, 'html.parser')
                
                # Extract product details
                title = soup.select_one('.private-product-detail__description').get_text(strip=True)
                format_size = ' '.join([span.get_text(strip=True) for span in soup.select('.product-format__size .headline1-r')])
                previous_price = soup.select_one('.product-price__previous-unit-price').get_text(strip=True)
                current_price = soup.select_one('.product-price__unit-price--discount').get_text(strip=True)
                units = soup.select_one('.product-price__extra-price').get_text(strip=True)
                allergens = soup.select_one('.private-product-detail__left').get('aria-label')
                
                # Find the last product-gallery__thumbnail element and get its link
                thumbnails = driver.find_elements(By.CSS_SELECTOR, ".product-gallery__thumbnail img")
                if thumbnails:
                    url_img = thumbnails[-1]
                    url_img = url_img.get_attribute("src")
                    url_img = url_img.replace("h=300", "h=1600").replace("w=300", "w=1600") #Change the resolution to be able to read it.
                else:
                    url_img = ''
                
                # Write the product details to the CSV file
                writer.writerow([
                    categorie or '',
                    subcategorie or '',
                    title or '',
                    format_size or '',
                    (previous_price + units) or '',
                    (current_price + units) or '',
                    units or '',
                    allergens or '',
                    url_img or ''
                ])
                
                # Print extracted details
                print(f"Title: {title}")
                print(f"Format Size: {format_size}")
                print(f"Previous Price: {previous_price}{units}")
                print(f"Current Price: {current_price}{units}")
                print(f"Allergens and other info: {allergens}")
                print(f"Last thumbnail link: {url_img}")
                
                # Navigate back to the categories page
                driver.back()
                time.sleep(3)  # Adjust sleep time as necessary to ensure the page loads
                
    except Exception as e:
        print(f"Error clicking product cells: {e}")
            



def iterate_categories_and_subheads(driver, skip_no_food=True):
    try:
        # Wait for the category menu to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".category-menu"))
        )
        
        category_items = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".category-menu__item"))
        )
        
        for category_item in category_items:
            # Click the category to open it
            header_button = WebDriverWait(category_item, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".collapse > button"))
            )

            # Skip non food categories
            if skip_no_food and header_button.text in ["Agua y refrescos", "Bebé", "Bodega", "Cuidado del cabello", 
                                                        "Cuidado facial y corporal", "Fitoterapia y parafarmacia", 
                                                        "Limpieza y hogar", "Maquillaje", "Mascotas"
                                                        ]:  
                continue

            header_button.click()
            time.sleep(2)  # Adjust sleep time as necessary to ensure the subheads load
            
            # Now iterate over each subhead within the opened category
            subheads = WebDriverWait(category_item, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".category-item"))
            )
            for subhead in subheads:
                subhead_button = subhead.find_element(By.CSS_SELECTOR, ".category-item__link")
                subhead_button.click()
                subhead_text = subhead_button.text
                print(f"Scraping: {subhead_text}")
                time.sleep(3)
                press_each_product_cell(driver, header_button.text, subhead_button.text)
                
            time.sleep(2)  # Adjust sleep time as necessary to ensure the category closes
            
    except Exception as e:
        print(f"Error iterating categories and subheads: {e}")




if __name__ == "__main__":
    postal_code = "23009"
    driver = open_categories_mercadona(postal_code)
    time.sleep(3)
    iterate_categories_and_subheads(driver)
    #press_each_product_cell(driver)
    # pageSource = driver.page_source
    # with open("mercadona_categories.html", "w", encoding="utf-8") as file:
    #     file.write(pageSource)
    driver.close()
        