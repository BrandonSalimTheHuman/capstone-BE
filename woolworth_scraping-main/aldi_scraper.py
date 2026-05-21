import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import json

URL = "https://www.aldi.com.au/products"


def scrape_aldi_specials(headless=False):
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    

    if headless:
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')  # maximize_window() is a no-op in headless

    options.add_argument('--log-level=3')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = webdriver.Chrome(service=service, options=options)
    if not headless:
        driver.maximize_window()

    driver.get(URL)

    loc_wait = WebDriverWait(driver, 8)

    # Press location change button
    try:
        change_address_button = loc_wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-mn="merchant-change-button"]'))
        )
        change_address_button.click()
        time.sleep(1)
    except TimeoutException:
        print("Location change button not found, proceeding without location selection")

    # Proceed to merchant search
    try:
        proceed_button = loc_wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-mn="merchant-change-confirm"]'))
        )
        proceed_button.click()
        time.sleep(1)
    except TimeoutException:
        print("Proceed button not found")

    # Type store name into search box
    try:
        search_box = loc_wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-mn="merchant-search-box"]'))
        )
        search_box.send_keys("Fairy Meadow")
        time.sleep(1)
    except TimeoutException:
        print("Store search box not found")

    # Select the Fairy Meadow store from results
    try:
        store_btn = loc_wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[aria-label="Select Store ALDI Fairy Meadow"]'))
        )
        store_btn.click()
        time.sleep(2)
    except TimeoutException:
        print("Fairy Meadow store result not found, proceeding anyway")

    # Main scraping logic
    products_data = []
    page_counter = 0

    while True:
        try:
            page_counter += 1
            driver.get(f'{URL}?page={page_counter}')

            print("Waiting for product tiles to load...")
            long_wait = WebDriverWait(driver, 20)
            product_tile_hosts = long_wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.product-tile__link'))
            )
                
            print(f"Found {len(product_tile_hosts)} product tiles on the page.")

            for host in product_tile_hosts:
                retries = 3
                while retries > 0:
                    try:
                        # shadow_root = get_shadow_root(driver, host)
                        name = host.find_element(By.CSS_SELECTOR, '.product-tile__name').text.strip()
                        price = host.find_element(By.CSS_SELECTOR, '.base-price__regular').text.strip()
                                    
                        try:
                            unit_price = host.find_element(By.CSS_SELECTOR, '.product-tile__comparison-price').text.strip()[1:-1]
                        except NoSuchElementException:
                            unit_price = "N/A"
                        
                        if unit_price == '' or unit_price is None:
                            unit_price = "N/A"

                        img = host.find_element(By.CSS_SELECTOR, '.base-image').get_attribute('src')

                        products_data.append({'Product Name': name, 'Price': price, 'Unit Price': unit_price, "Image url": img})
                        break
                        
                    except (NoSuchElementException, AttributeError):
                               break
                    except StaleElementReferenceException: 
                        retries -= 1
                        print(f"Stale element encountered. Retrying item... ({retries} retries left)")
                        if retries == 0:
                            print("Failed to scrape this item after multiple attempts. Skipping item.")
                    break # Skip to next item
                 
        except TimeoutException:
            print("Timeout waiting for product tiles. Assuming end of pages.")
            break 
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break
          
    unique_products = [
        json.loads(element) for element in set(
        json.dumps(data) for data in products_data
    )]

    print("Closing browser.")
    driver.quit()
        
    return unique_products

if __name__ == "__main__":
    import argparse
    import db_upload

    parser = argparse.ArgumentParser(description="Scrape Aldi and upload to DB")
    parser.add_argument('--headless', action='store_true',
                        help="Run Chrome in headless mode (required for CI)")
    args = parser.parse_args()

    print("Scraping Aldi...")
    scraped_data = scrape_aldi_specials(headless=args.headless)

    if scraped_data:
        print(f"Scraped {len(scraped_data)} products. Uploading to database...")
        db_upload.upload_products(scraped_data, "Aldi")
    else:
        print("Scraping returned no data.")
        raise SystemExit(1)