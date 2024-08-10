from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
import shutil
import csv
import time

def load_chrome_webdriver(headless=False):
    """Loads a Chrome webdriver with specified options.

    Args:
        headless (bool, optional): Whether to run the browser in headless mode. Defaults to False.

    Returns:
        webdriver.Chrome: The Chrome webdriver instance.
    """
    options = Options()
    options.add_argument("--disable-search-engine-choice-screen")  # Avoid having to choose a default browser
    options.add_argument("--incognito")  # Open in incognito mode to avoid saving cookies and cache
    options.add_argument("--disable-extensions")  # Disable extensions
    options.add_argument("--headless") if headless else None
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def open_categories_mercadona(postal_code, headless=False):
    """Opens the Mercadona categories page and handles cookies and postal code input.

    Args:
        postal_code (str): The postal code to use for location-based results.
        headless (bool, optional): Whether to run the browser in headless mode. Defaults to False.

    Returns:
        webdriver.Chrome: The Chrome webdriver instance.
    """
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
    """Parses a product string to extract container, price value, and price unit.

    Args:
        product_string (str): The product string to parse.

    Returns:
        tuple: A tuple containing the container, price value, and price unit.
               Returns (product_string, None, None) if parsing fails.
    """
    try:
        # Split the string by the '|' separator
        parts = product_string.split('|')

        # Extract the container information
        container = parts[0].strip()

        # Extract the price and price unit
        price_info = parts[1].strip()
        price_value, price_unit = price_info.split('/')
        price_value = price_value.replace(',', '.')

        # Return the desired output
        return container, price_value, price_unit
    except Exception as e:
        error_message = f"Error parsing the format: {e}\n"
        with open('errors.log', 'a') as error_file:
            error_file.write(error_message)
        return product_string, None, None


def get_last_product():
    """Retrieves the last product scraped from the CSV file.

    Returns:
        tuple: A tuple containing the category, subcategory, and product name of the last product.
               Returns (None, None, None) if the file doesn't exist or is empty.
    """
    if os.path.exists('mercadona.csv'):
        with open('mercadona.csv', 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter='$')
            last_row = None
            for row in reader:
                last_row = row
            if last_row:
                return last_row[0], last_row[1], last_row[2]  # category, subcategory, product name
    return None, None, None


def press_each_product_cell(driver, category, subcategory, last_product=None):
    """Iterates through product cells, extracts product details, and writes them to a CSV file.

    The CSV file has a row for each product and contains the following columns:
        - category: The category of the product.
        - subcategory: The subcategory of the product.
        - product name: The name of the product.
        - container: The container of the product.
        - price value: The price value of the product.
        - price unit: The price unit of the product.
        - description: The description of the product.
        - link: The link to the image of the product.

    Args:
        driver (webdriver.Chrome): The Chrome webdriver instance.
        category (str): The current category being scraped.
        subcategory (str): The current subcategory being scraped.
        last_product (str, optional): The name of the last product scraped in a previous run.
                                       Used for resuming the scraping process. Defaults to None.
    """
    resume_mode = last_product is not None

    with open('mercadona.csv', mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter='$')

        if os.path.getsize('mercadona.csv') == 0:
            writer.writerow(['category', 'subcategory', 'product name', 'container', 'price value', 'price unit', 'description', 'link'])

        product_cells = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-container .product-cell--actionable"))
        )
        for cell in product_cells:
            try:
                # Try to get the product name using different possible selectors
                product_name = None
                for selector in ['.product-cell__description', '.product-cell__name', 'h4']:
                    try:
                        product_name = cell.find_element(By.CSS_SELECTOR, selector).text
                        if product_name:
                            break
                    except:
                        continue

                if not product_name:
                    print("Could not find product name, skipping...")
                    continue

                if resume_mode:
                    if product_name == last_product:
                        resume_mode = False
                        continue  # Skip this product to avoid duplication
                    else:
                        continue

                # Save the current webpage link before clicking the cell in case of an error
                current_url = driver.current_url

                cell.click()
                # Wait for the product details to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.private-product-detail__description'))
                )
                time.sleep(5)  # Adjust sleep time as necessary

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
                    url_img = url_img.replace("h=300", "h=1600").replace("w=300", "w=1600")  # Change the resolution to be able to read it.
                else:
                    url_img = ''

                # Write the product details to the CSV file
                writer.writerow([
                    category or '',
                    subcategory or '',
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

                # Wait for the categories page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".category-menu"))
                )
                time.sleep(5)  # Adjust sleep time as necessary to ensure the page loads

            except Exception as e:
                error_message = f"Error clicking product cells: {e}\n"
                if 'product_name' in locals():
                    error_message += f"Product name: {product_name}\n"
                with open('errors.log', 'a') as error_file:
                    error_file.write(error_message)
                print(error_message)

                # Save the current HTML to the error htmls folder with a unique name
                html_filename = f"error_{category}_{subcategory}_{int(time.time())}.html"
                with open(os.path.join('error_htmls', html_filename), 'w', encoding='utf-8') as html_file:
                    html_file.write(driver.page_source)

                # Return to the saved URL if an error occurs
                driver.get(current_url)
                continue


def iterate_categories_and_subcategories(driver, skip_no_food=True):
    """Iterates through categories and subcategories on the Mercadona website, scraping product data.

    Args:
        driver (webdriver.Chrome): The Chrome webdriver instance.
        skip_no_food (bool, optional): Whether to skip non-food categories. Defaults to True.
    """
    last_category, last_subcategory, last_product = get_last_product()
    resume_mode = last_product is not None

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

                # Skip non-food categories
                if skip_no_food and header_button.text in [
                    "Agua y refrescos", "Bebé", "Bodega", "Cuidado del cabello",
                    "Cuidado facial y corporal", "Fitoterapia y parafarmacia",
                    "Limpieza y hogar", "Maquillaje", "Mascotas"
                                                          ]:
                    continue

                if resume_mode and header_button.text != last_category:
                    continue

                header_button.click()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".category-item"))
                )
                time.sleep(5 if resume_mode else 600)  # Adjust sleep time as necessary to ensure the subheads load

                # Now iterate over each subhead within the opened category
                subheads = WebDriverWait(category_item, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".category-item"))
                )
                for subhead in subheads:
                    try:
                        subhead_button = subhead.find_element(By.CSS_SELECTOR, ".category-item__link")

                        if resume_mode and subhead_button.text != last_subcategory:
                            continue

                        subhead_button.click()
                        # Wait for the product grid to load
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".product-container .product-cell--actionable"))
                        )
                        subhead_text = subhead_button.text
                        print(f"Scraping: {subhead_text}")
                        time.sleep(120)

                        press_each_product_cell(driver, header_button.text, subhead_button.text, last_product if resume_mode else None)

                        if resume_mode:
                            resume_mode = False
                            last_product = None
                    except Exception as e:
                        error_message = f"Error processing subhead: {e}\n"
                        if 'subhead_text' in locals():
                            error_message += f"Subcategory: {subhead_text}\n"
                        with open('errors.log', 'a') as error_file:
                            error_file.write(error_message)
                        print(error_message)
                        continue  # Skip to the next subhead

                time.sleep(5)  # Adjust sleep time as necessary to ensure the category closes
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
    """Removes specified files or folders if they exist.

    Args:
        files_to_delete (list): A list of file or folder paths to delete.
    """
    for file in files_to_delete:
        try:
            if os.path.exists(file):
                if os.path.isfile(file):
                    os.remove(file)
                    print(f"Deleted file: {file}")
                elif os.path.isdir(file):
                    shutil.rmtree(file)
                    print(f"Deleted folder: {file}")
        except Exception as e:
            print(f"Error deleting {file}: {e}")

if __name__ == "__main__":
    start_time = time.time()

    # Get postal code from user input
    while True:
        postal_code = input("Enter your 5-digit postal code: ")
        if len(postal_code) == 5 and postal_code.isdigit():
            break
        else:
            print("Invalid postal code. Please enter a 5-digit number.")

    # Ask the user if they want to delete the error files
    delete_error_files = input("Do you want to delete error files (errors.log and ./error_htmls)? (y/n): ")

    # Delete error files if the user chooses to
    if delete_error_files.lower() == 'y':
        remove_execution_files(['errors.log', './error_htmls'])

    driver = open_categories_mercadona(postal_code, headless=True)
    time.sleep(3)
    iterate_categories_and_subcategories(driver)
    driver.close()

    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes = int(elapsed_time / 60)
    seconds = int(elapsed_time % 60)
    print(f"The program took {minutes:02d}:{seconds:02d} minutes to execute.")