import time
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

def scroll(driver):
    # get scrollable height
    total_height = driver.execute_script("return document.body.scrollHeight")
    # simulate slow scrolling
    for i in range(0, (round(total_height * random.random())), random.randint(400, 700)):
        driver.execute_script(f"window.scrollTo(0, {i});")
        time.sleep(random.uniform(0.25, 0.45))

def scrape_coles(part=None, headless=False):
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
        # create a random fake user agent
        ua = UserAgent()
        user_agent = ua.random
        options.add_argument(f'user-agent={user_agent}')
        driver = uc.Chrome(options=options)
        driver.maximize_window()

    products_data = []

    time.sleep(2)

    driver.get('https://www.coles.com.au/browse')

    long_wait = WebDriverWait(driver, 60)
    category_containers= long_wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.coles-targeting-ShopCategoriesShopCategoryStyledCategoryContainer'))
    )

    urls = []

    for container in category_containers:
        url = container.get_attribute('href')
        urls.append(url)

    if part == 1:
        urls = urls[:len(urls) // 2]
    elif part == 2:
        urls = urls[len(urls) // 2:]

    for url in urls:
        page_counter = 0
        while True:
            try:
                page_start_time = time.time()
                page_counter += 1
                driver.get(f'{url}?page={page_counter}')

                # sleep for some time
                time.sleep(random.uniform(0.3, 1.3))

                scroll(driver)

                print("Waiting for product tiles to load...")
                long_wait = WebDriverWait(driver, 20)
                product_tile_hosts = long_wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.list-item:not(.single-tile-ad)'))
                )

                print(f"Found {len(product_tile_hosts)} product tiles on the page.")

                for i, host in enumerate(product_tile_hosts):
                    try:
                        if i%6 == 0:
                            # I sleep
                            time.sleep(random.uniform(0.1, 0.3))

                        title_area = host.find_element(By.CSS_SELECTOR, '.product__message-title_area')
                        name = title_area.find_element(By.CSS_SELECTOR, '.sr-only').text.strip()
                        # name = host.find_element(By.CSS_SELECTOR, '.product__title').text.strip()
          
                        price = host.find_element(By.CSS_SELECTOR, '.price__value').text.strip()
          
                        try:
                            unit_price = host.find_element(By.CSS_SELECTOR, '.price__calculation_method').text.strip().split('|')[0].strip().split('\n')[0].strip()
                        except NoSuchElementException:
                            unit_price = "N/A"

                        try:
                            complex_discount_text = host.find_element(By.CSS_SELECTOR, '[data-testid="complex-promotion-link"]').text.strip().split()
                            for i in range(len(complex_discount_text)):
                                if complex_discount_text[i] == 'for':
                                    complex_discount = {'Quantity': complex_discount_text[i-1], 'Price': complex_discount_text[i+1][1:]}
                        except NoSuchElementException:
                            complex_discount = "N/A"
                        
                        img = host.find_element(By.CSS_SELECTOR, '[data-testid="product-image"]').get_attribute('src')

                        products_data.append({'Product Name': name, 'Price': price, 'Unit Price': unit_price, 'Complex Discount': complex_discount, 'Image': img})
                    except (NoSuchElementException, AttributeError):
                        continue
                    except StaleElementReferenceException: 
                            print("Stale element encountered")
                            page_counter -= 1
                            break

            except TimeoutException:
                print("Timeout waiting for product tiles. Assuming end of pages.")
                break 
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                break
            
            end_time = time.time()
            while end_time - page_start_time < 14:
                time.sleep(random.uniform(0.5, 3.5))
                end_time = time.time()

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

    parser = argparse.ArgumentParser(description="Scrape Coles and upload to DB")
    parser.add_argument('--part', type=int, choices=[1, 2], default=None,
                        help="Scrape only the first (1) or second (2) half of categories")
    parser.add_argument('--headless', action='store_true',
                        help="Run Chrome in headless mode (required for CI)")
    args = parser.parse_args()

    part_label = f" (part {args.part})" if args.part else ""
    print(f"Scraping Coles{part_label}...")
    scraped_data = scrape_coles(part=args.part, headless=args.headless)

    if scraped_data:
        print(f"Scraped {len(scraped_data)} products. Uploading to database...")
        db_upload.upload_products(scraped_data, "Coles")
    else:
        print("Scraping returned no data.")
        raise SystemExit(1)