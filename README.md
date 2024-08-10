# Mercadona Products Scrapper

> **Important Notice - Last Updated: August 10, 2024**
>
> This scraper was last updated on **August 10, 2024**.  Be aware that significant changes to Mercadona's website structure might render this scraper non-functional.

> **CSV Delimiter**
>
> The output CSV file (`mercadona.csv`) uses the unconventional delimiter `$` to separate fields. This ensures compatibility with product descriptions that may contain `,` `;` `:` `/` ...

This project is a personal web scraper designed to extract product information from the [Mercadona website](https://tienda.mercadona.es/) (a well-known Spanish supermarket). The primary motivation behind this project is to gather data for a Menu Planning Problem (MPP). This is not affiliated with Mercadona in any way.

## Libraries Used

This project leverages the power of the following Python libraries:

* **Selenium:** Used for automating web browser interactions.
* **Beautiful Soup:** Used for parsing HTML content.

## How to Use

1. **Install Required Libraries:**
   ```bash
   pip install selenium beautifulsoup4 webdriver_manager
   ```

2. **Run the Script:**
   ```bash
   python MercadonaScraper.py
   ```

3. **Enter Postal Code:**
   Upon execution, the script will prompt you to enter your 5-digit postal code. This is necessary to access location-specific product information.

4. **Choose to Delete Error Files (Optional):**
   You will be asked if you want to delete any existing error files that might have been created in a previous execution (`errors.log` and the `./error_htmls` folder).

5. **Output:**
   The script will create a CSV file named `mercadona.csv` containing the scraped product data. The file includes the following columns:

   * `category`: The product's main category.
   * `subcategory`: The product's specific subcategory.
   * `product name`: The name of the product.
   * `container`: Information about the product's packaging (e.g., weight, quantity).
   * `price value`: The numerical price of the product.
   * `price unit`: The unit of the price (e.g., €/kg, €/ud).
   * `description`: A brief description of the product.
   * `link`: A direct link to the product's nutritional label image.

   **Note:** Only food-related products are scraped.

6. **Error Handling:**
   The script includes error handling and may generate the following files in case of issues:

   * `errors.log`: A log file containing error messages.
   * `./error_htmls`: A folder containing HTML snapshots of pages where errors occurred.

## References

*  [**Web Scraping with Python**  by Ryan Mitchell](https://www.oreilly.com/library/view/web-scraping-with/9781098145347/)

## Acknowledgements

Special thanks to the following Large Language Models (LLMs) for their assistance in developing the code:

* Claude 3.5
* GPT-4
* Gemini 1.5 Pro Experimental
