import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from fake_useragent import UserAgent
import undetected_chromedriver as uc
import json
import random
import db_upload

def scroll(driver):
    # get scrollable height
    total_height = driver.execute_script("return document.body.scrollHeight")
    # simulate slow scrolling
    for i in range(0, (round(total_height * random.random())), random.randint(400, 700)):
        driver.execute_script(f"window.scrollTo(0, {i});")
        time.sleep(random.uniform(0.2, 0.4))

def scrape_iga(part=None, headless=False):
    options = uc.ChromeOptions()
    options.add_argument('--log-level=3')

    if headless:
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        driver = uc.Chrome(options=options, headless=True)
    else:
        driver = uc.Chrome(options=options)
        driver.maximize_window()

    products_data = []

    driver.get('https://www.igashop.com.au/')

    long_wait = WebDriverWait(driver, 20)
    location_field = long_wait.until(
        EC.presence_of_all_elements_located((By.ID, 'store-reminder-location'))
    )

    location_field = driver.find_element(By.ID, "store-reminder-location")
    location_field.send_keys("Mt Cotton")   

    time.sleep(2)

    long_wait = WebDriverWait(driver, 20)
    correct_location = long_wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-test-id="address-finder-result-1"]'))
    )

    correct_location = driver.find_element(By.CSS_SELECTOR, '[data-test-id="address-finder-result-1"]')
    correct_location.click()

    time.sleep(2)

    long_wait = WebDriverWait(driver, 20)
    store_id = long_wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-store-id="84971"]'))
    )

    select_button = driver.find_element(By.CSS_SELECTOR, '[data-store-id="84971"] button')

    select_button.click()

    time.sleep(2)

    long_wait = WebDriverWait(driver, 20)
    category_containers= long_wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-test-id^="category-navigation-item"]'))
    )

    time.sleep(2)

    category_urls = []

    for container in category_containers:
        while True:
            try:
                url = container.get_attribute('href')
                if url is None:
                    category_name = container.text.strip()
                    category_name = '-'.join(category_name.lower().replace(',', '').split())
                    category_urls.append(f'https://www.igashop.com.au/categories/{category_name}')
                else:
                    category_urls.append(url)
                break
            except StaleElementReferenceException: 
                print("Stale")
                   
    
    # Temporary
    print(category_urls)

    final_urls = []

    for category in category_urls:
        driver.get(category)
        long_wait = WebDriverWait(driver, 20)
        subcategories = []
        while True:
            try:
                subcategories = long_wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".min-w-fit.snap-start a"))
                )
                break
            except TimeoutException:
                print("Timeout, assuming no subcategories")
                category = category[:-2]
                break
            except StaleElementReferenceException:
                print("Stale")

        if len(subcategories) == 0:
            final_urls.append(category)
        else:
            for subcategory in subcategories:
                final_urls.append(subcategory.get_attribute("href"))
                
        time.sleep(random.uniform(1, 3))


    if part == 1:
        final_urls = final_urls[:len(final_urls) // 2]
    elif part == 2:
        final_urls = final_urls[len(final_urls) // 2:]

    for url in final_urls:
        page_counter = 0
        last_problem_page = -1
        newly_added_items = []
        while True:
            try:
                page_counter += 1
                driver.get(f'{url}/{page_counter}')

                # sleep for some time
                time.sleep(random.uniform(0.5, 1.5))

                scroll(driver)

                print("Waiting for product tiles to load...")
                long_wait = WebDriverWait(driver, 30)
                product_tiles = long_wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-product-card="true"]'))
                )

                print(f"Found {len(product_tiles)} product tiles on the page.")

                for i, host in enumerate(product_tiles):
                    try:
                        if i%6 == 0:
                            # I sleep
                            time.sleep(random.uniform(0.05, 0.25))
                        
                        key_text = host.find_elements(By.CSS_SELECTOR, 'span')
                      
                        if len(key_text) == 2:
                            name = f"{key_text[0].text.strip()}"
                            price = f"{key_text[1].text.strip()}"
                        else:
                            name = f"{key_text[0].text.strip()} {key_text[1].text.strip()}"
                            price = key_text[2].text.strip()
                        if len(key_text) > 4:
                            key_text[4] = key_text[4].text.replace("per", "")
                            unit_price = f"{key_text[3].text.strip()}/{key_text[4].strip()}"
                        elif len(key_text) > 3:
                            unit_price = key_text[3].text.strip()
                        else:
                            unit_price = "N/A"
        
                        
                        img = host.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')

                        newly_added_items.append({'Product Name': name, 'Price': price, 'Unit Price': unit_price, 'Image': img})
    
                    except (NoSuchElementException, AttributeError):
                        continue
                    except StaleElementReferenceException: 
                            print("Stale element encountered")
                            page_counter -= 1
                            break
                
                check = True
                for item in newly_added_items:
                    if item not in products_data:
                        check = False
                        products_data.append(item)
                
                newly_added_items = []
                
                if check:
                    break

            except TimeoutException:
                print("Timeout waiting for product tiles. Assuming end of pages.")
                if page_counter != last_problem_page:
                    last_problem_page = page_counter
                    page_counter -= 1
                    time.sleep(60)
                else:
                    break 
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                return None

    unique_products = [
    json.loads(element) for element in set(
        json.dumps(data) for data in products_data
    )]
    
    print("Closing browser.")
    driver.quit()

    return unique_products

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape IGA and upload to DB")
    parser.add_argument('--part', type=int, choices=[1, 2], default=None,
                        help="Scrape only the first (1) or second (2) half of categories")
    parser.add_argument('--headless', action='store_true',
                        help="Run Chrome in headless mode (required for CI)")
    args = parser.parse_args()

    part_label = f" (part {args.part})" if args.part else ""
    print(f"Scraping IGA{part_label}...")
    scraped_data = scrape_iga(part=args.part, headless=args.headless)

    if scraped_data:
        print(f"Scraped {len(scraped_data)} products. Uploading to database...")
        db_upload.upload_products(scraped_data, "IGA")
    else:
        print("Scraping returned no data.")
        raise SystemExit(1) 