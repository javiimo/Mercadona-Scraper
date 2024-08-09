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

def open_categories_mercadona(postal_code, headless=False):
    driver = load_chrome_webdriver(headless)
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



def parse_product_info(product_string):
    try: 
        # Split the string by the '|' separator
        parts = product_string.split('|')
        
        # Extract the container information
        container = parts[0].strip()
        
        # Extract the price and price unit
        price_info = parts[1].strip()
        price_value, price_unit = price_info.split('/')
        price_value = price_value.replace(',', '.')
            
        # Convert the price_per_liter to a string without the comma
        price_value = price_value.replace(',', '.')
        
        # Return the desired output
        return container, price_value, price_unit
    except Exception as e:
        error_message = f"Error parsing the format: {e}\n"
        with open('errors.log', 'a') as error_file:
            error_file.write(error_message)
        return product_string, None, None



def press_each_product_cell(driver, categorie, subcategorie):
    try:
        # Check if the file exists and is not empty
        file_exists = os.path.isfile('mercadona.csv') and os.path.getsize('mercadona.csv') > 0

        with open('mercadona.csv', mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter='$') #! Notice the $ separator to make sure it is not contained in the description of the product
            
            # Write the header row only if the file is empty
            if not file_exists:
                writer.writerow(['categorie', 'subcategorie', 'product name', 'container', 'price value', 'price unit', 'description', 'link'])

            product_cells = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-container .product-cell--actionable"))
                        )
            for cell in product_cells:
                try:
                    # Save the current webpage link before clicking the cell in case of an error
                    current_url = driver.current_url
                    
                    cell.click()
                    time.sleep(3)  # Adjust sleep time as necessary
                    
                    # Get page source
                    pageSource = driver.page_source
                    
                    # Parse the page source with BeautifulSoup
                    soup = BeautifulSoup(pageSource, 'html.parser')
                    
                    # Extract product details
                    product_name = soup.select_one('.private-product-detail__description').get_text(strip=True)
                    format = ' '.join([span.get_text(strip=True) for span in soup.select('.product-format__size .headline1-r')])
                    description = soup.select_one('.private-product-detail__left').get('aria-label')
                    
                    # Parse format into several categories
                    container, price_value, price_unit = parse_product_info(format)

                    # Find the last product-gallery__thumbnail element and get its link
                    thumbnails = driver.find_elements(By.CSS_SELECTOR, ".product-gallery__thumbnail img")
                    if thumbnails:
                        url_img = thumbnails[-1]
                        url_img = url_img.get_attribute("src")
                        url_img = url_img.replace("h=300", "h=1600").replace("w=300", "w=1600") # Change the resolution to be able to read it.
                    else:
                        url_img = ''
                    
                    # Write the product details to the CSV file
                    writer.writerow([
                        categorie or '',
                        subcategorie or '',
                        product_name or '',
                        container or '',
                        price_value or '',
                        price_unit or '',
                        description or '',
                        url_img or ''
                    ])
                    
                    # Print what was added to the csv
                    print(f"Added {product_name}")
                    
                    # Navigate back to the categories page
                    driver.back()
                    time.sleep(3)  # Adjust sleep time as necessary to ensure the page loads

                except Exception as e:
                    error_message = f"Error clicking product cells: {e}\n"
                    if 'product_name' in locals():
                        error_message += f"Product name: {product_name}\n"
                    with open('errors.log', 'a') as error_file:
                        error_file.write(error_message)
                    print(error_message)
                    
                    # Save the current HTML to the error htmls folder with a unique name
                    html_filename = f"error_{categorie}_{subcategorie}_{int(time.time())}.html"
                    with open(os.path.join('error_htmls', html_filename), 'w', encoding='utf-8') as html_file:
                        html_file.write(pageSource)
                    
                    # Return to the saved URL if an error occurs
                    driver.get(current_url)
                    continue
    except Exception as e:
        error_message = f"Error in press_each_product_cell: {e}\n"
        with open('errors.log', 'a') as error_file:
            error_file.write(error_message)
        print(error_message)
            



def iterate_categories_and_subcategories(driver, skip_no_food=True):
    try:
        # Wait for the category menu to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".category-menu"))
        )
        
        category_items = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".category-menu__item"))
        )
        
        for category_item in category_items:
            try:
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
                    try:
                        subhead_button = subhead.find_element(By.CSS_SELECTOR, ".category-item__link")
                        subhead_button.click()
                        subhead_text = subhead_button.text
                        print(f"Scraping: {subhead_text}")
                        time.sleep(3)
                        press_each_product_cell(driver, header_button.text, subhead_button.text)
                    except Exception as e:
                        error_message = f"Error processing subhead: {e}\n"
                        if 'subhead_text' in locals():
                            error_message += f"Subcategory: {subhead_text}\n"
                        with open('errors.log', 'a') as error_file:
                            error_file.write(error_message)
                        print(error_message)
                        continue  # Skip to the next subhead
                    
                time.sleep(2)  # Adjust sleep time as necessary to ensure the category closes
            except Exception as e:
                error_message = f"Error iterating categories and subcategories: {e}\n"
                if 'subhead_text' in locals():
                    error_message += f"Subcategory: {subhead_text}\n"
                with open('errors.log', 'a') as error_file:
                    error_file.write(error_message)
                print(error_message)

    except Exception as e:
        error_message = f"Error at getting the category menu: {e}\n"
        if 'subhead_text' in locals():
            error_message += f"Subcategory: {subhead_text}\n"
        with open('errors.log', 'a') as error_file:
            error_file.write(error_message)
        print(error_message)


def remove_execution_files(files_to_delete):
    for file in files_to_delete:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"Deleted: {file}")
        except Exception as e:
            print(f"Error deleting file {file}: {e}")

if __name__ == "__main__":
    # Delete mercadona.csv and errors.log if they exist
    remove_execution_files(['mercadona.csv', 'errors.log'])
    postal_code = "23009"
    driver = open_categories_mercadona(postal_code, headless=True)
    time.sleep(3)
    iterate_categories_and_subcategories(driver)
    # pageSource = driver.page_source
    # with open("mercadona_categories.html", "w", encoding="utf-8") as file:
    #     file.write(pageSource)
    driver.close()
        