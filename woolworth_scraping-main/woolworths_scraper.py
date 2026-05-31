import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, DetachedShadowRootException, ElementClickInterceptedException
import undetected_chromedriver as uc
import re
import random

URL = "https://www.woolworths.com.au"

def get_shadow_root(driver, host_element):
    return driver.execute_script('return arguments[0].shadowRoot', host_element)

def scrape_woolworths_specials(part=None, headless=False):
    options = uc.ChromeOptions()
    options.add_argument('--log-level=3')

    chrome_major_version = os.environ.get('CHROME_MAJOR_VERSION')
    if chrome_major_version:
        chrome_major_version = int(chrome_major_version)

    if headless:
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        driver = uc.Chrome(options=options, headless=True, version_main=chrome_major_version)
    else:
        driver = uc.Chrome(options=options, version_main=148)
        driver.maximize_window()
        
    products_data = []
    
    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20) 

        long_wait = WebDriverWait(driver, 20)
        while True:
            try:
                browse_categories_buttons = long_wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[aria-label="`Browse"]')))
                browse_categories_button = driver.find_element(By.CSS_SELECTOR, '[aria-label="`Browse"]')
                break
            except StaleElementReferenceException: 
                print("Stale element encountered")
                print("Trying again")

        browse_categories_button.click()

        long_wait = WebDriverWait(driver, 20)
        category_list = []
        while True:
            try:
                categories_exist = long_wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.description')))
                categories = driver.find_elements(By.CSS_SELECTOR, '.description')
                for category in categories:
                    category_list.append(category.text.strip())
                break
            except StaleElementReferenceException: 
                print("Stale element encountered")
                print("Trying again")

        category_urls = []
        for category in category_list:
            cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', category.lower())
            category_url = "-".join(cleaned.split())
            category_urls.append(category_url)
        
        category_urls = category_urls[1:-1]

        if part == 1:
            category_urls = category_urls[:len(category_urls) // 2]
        elif part == 2:
            category_urls = category_urls[len(category_urls) // 2:]

        # while True:
        #     driver.get("https://www.woolworths.com.au/shop/browse/fruit-veg")
        #     try:
        #         long_wait = WebDriverWait(driver, 20)
        #         try:
        #             right_arrow_load = long_wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.chip-nav-arrow.right')))
        #             right_arrow = driver.find_element(By.CSS_SELECTOR, '.chip-nav-arrow.right')
        #             right_arrow.click()
        #         except (NoSuchElementException, TimeoutException):
        #             print("Skipping right arrow")
        #         except ElementClickInterceptedException:
        #             print("Skipping right arrow (intercepted)")
        #         buttons_load = long_wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.chip-menu_core-chip-multiple__1rxiE')))
        #         buttons = driver.find_elements(By.CSS_SELECTOR, '.chip-menu_core-chip-multiple__1rxiE')
        #         for button in buttons:
        #             time.sleep(0.5)
        #             try:
        #                 button_text = button.find_element(By.CSS_SELECTOR, 'span')
        #             except NoSuchElementException:
        #                 continue
        #             if button_text.text.strip() == 'All filters':
        #                 button.click()
        #         break                   
        #     except StaleElementReferenceException: 
        #         print("Stale element encountered")
        #         print("Trying again")
            
        # while True:
        #     try:
        #         long_wait = WebDriverWait(driver, 20)
        #         buttons_load_1 = long_wait.until(EC.presence_of_all_elements_located((By.ID, '_r_49_')))
        #         button_1 = driver.find_element(By.ID, '_r_49_')
        #         button_1.click()
        #         time.sleep(0.5)
        #         buttons_load_2 = long_wait.until(EC.presence_of_all_elements_located((By.ID, '_r_4d_')))
        #         button_2 = driver.find_element(By.ID, '_r_4d_')
        #         button_2.click()
        #         time.sleep(0.5)
        #         confirm_button_load = long_wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.all-filter_component_all-filter-footer__gOA2q button')))
        #         confirm_buttons = driver.find_elements(By.CSS_SELECTOR, '.all-filter_component_all-filter-footer__gOA2q button')
        #         for button in confirm_buttons:
        #             if button.text.strip() == 'See results':
        #                 button.click()
        #                 break
        #         break                   
        #     except StaleElementReferenceException: 
        #         print("Stale element encountered")
        #         print("Trying again")


        for category_url in category_urls:
            page_counter = 0
            newly_added_items = []
            while True:
                page_counter += 1
                driver.get(f'{URL}/shop/browse/{category_url}?excludeUnavailableProducts=true&isHideEverydayMarketProducts=true&pageNumber={page_counter}')
                print("Waiting for product tiles to load...")
                long_wait = WebDriverWait(driver, 30)
                product_tile_hosts = long_wait.until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, 'wc-product-tile'))
                )
                
                print(f"Found {len(product_tile_hosts)} product tiles on the page.")

                stale = False

                for host in product_tile_hosts:
                    try:
                        # random sleeping
                        if random.random() < 0.3:
                            time.sleep(random.uniform(0.25, 1))
                        
                        # get shadow root
                        shadow_root = get_shadow_root(driver, host)

                        time.sleep(0.05)

                        # product name
                        name = shadow_root.find_element(By.CSS_SELECTOR, '.product-title-container .title').text.strip()

                        # product price
                        try:
                            full_price = shadow_root.find_element(By.CSS_SELECTOR, 'div.primary').text.strip()
                            price = full_price.split()[0]
                        except NoSuchElementException:
                            continue

                        # product unit price
                        try:
                            unit_price = shadow_root.find_element(By.CSS_SELECTOR, 'span.price-per-cup').text.strip()
                        except NoSuchElementException:
                            unit_price = "N/A" 

                        # product promo
                        try:
                            promo_area = shadow_root.find_element(By.CSS_SELECTOR, '.product-tile-promo-info')
                            try:
                                complex_discount = promo_area.find_element(By.TAG_NAME, 'span')
                                complex_discount_words = complex_discount.text.lower().strip().split()
                                check = False
                                if len(complex_discount_words) == 3:
                                    for i in range(len(complex_discount_words)):
                                        if complex_discount_words[i] == 'for':
                                            complex_discount = {'Quantity': complex_discount_words[i-1], 'Price': complex_discount_words[i+1][1:]}
                                            check = True
                                    if not check:
                                        complex_discount = "N/A"
                                else:
                                    complex_discount = "N/A"
                            except NoSuchElementException:
                                complex_discount = "N/A"
                        except NoSuchElementException:
                            complex_discount = "N/A"
                        
                        # product image
                        img = shadow_root.find_element(By.CSS_SELECTOR, '.product-tile-image img').get_attribute('src')

                        # adding to newly added items
                        newly_added_items.append({'Product Name': name, 'Price': price, 'Unit Price': unit_price, 'Complex discount': complex_discount, 'Image': img})
                    except (NoSuchElementException, AttributeError):
                        continue
                    except (StaleElementReferenceException, DetachedShadowRootException): 
                        print("Stale element encountered")
                        # try again
                        page_counter -= 1
                        stale = True
                        break
                
                # if there wasn't an error, check if every item already exists. If so, the products is assumed to have run out, move to the next category
                if not stale:
                    check = True
                    for item in newly_added_items:
                        if item not in products_data:
                            check = False
                            products_data.append(item)
                    newly_added_items = []
                    if check:
                        break

    except TimeoutException:
        print("Scraping Interrupted: Timed out waiting for product tiles to appear.")
        return products_data
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return products_data
    finally:
        print("Closing browser.")
    
    try:
        driver.quit()
    except Exception:
        pass
    finally:
        del driver
        
    return products_data

if __name__ == "__main__":
    import argparse
    import db_upload

    parser = argparse.ArgumentParser(description="Scrape Woolworths and upload to DB")
    parser.add_argument('--part', type=int, choices=[1, 2], default=None,
                        help="Scrape only the first (1) or second (2) half of categories")
    parser.add_argument('--headless', action='store_true',
                        help="Run Chrome in headless mode (required for CI)")
    args = parser.parse_args()

    part_label = f" (part {args.part})" if args.part else ""
    print(f"Scraping Woolworths{part_label}...")
    scraped_data = scrape_woolworths_specials(part=args.part, headless=args.headless)

    if scraped_data:
        print(f"Scraped {len(scraped_data)} products. Uploading to database...")
        db_upload.upload_products(scraped_data, "Woolworths")
    else:
        print("Scraping returned no data.")
        raise SystemExit(1)