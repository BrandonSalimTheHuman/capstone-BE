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

def scroll(driver):
    # get scrollable height
    total_height = driver.execute_script("return document.body.scrollHeight")
    # simulate slow scrolling
    for i in range(0, (round(total_height * random.random())), random.randint(400, 700)):
        driver.execute_script(f"window.scrollTo(0, {i});")
        time.sleep(random.uniform(0.2, 0.4))

def scrape_coles():
    options = uc.ChromeOptions()
    options.add_argument('--log-level=3')

    # create a random fake user agent
    ua = UserAgent()
    user_agent = ua.random
    options.add_argument(f'user-agent={user_agent}')
    
    driver = uc.Chrome(options=options, version_main=144) 
    driver.maximize_window() 

    # seeing the navigator.webdriver property to false
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
            })
        """
    })

    products_data = []

    driver.get('https://www.coles.com.au/browse')

    long_wait = WebDriverWait(driver, 7)
    category_containers= long_wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.coles-targeting-ShopCategoriesShopCategoryStyledCategoryContainer'))
    )

    urls = []

    for container in category_containers:
        url = container.get_attribute('href')
        urls.append(url)

    # Temporary
    print(urls)
    urls = [urls[2]]

    for url in urls:
        page_counter = 0
        print(url)
        while True:
            try:
                page_start_time = time.time()
                page_counter += 1
                driver.get(f'{url}&page={page_counter}')

                # sleep for some time
                time.sleep(random.uniform(0.5, 1.5))

                scroll(driver)

                print("Waiting for product tiles to load...")
                long_wait = WebDriverWait(driver, 7)
                product_tile_hosts = long_wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.list-item:not(.single-tile-ad)'))
                )

                print(f"Found {len(product_tile_hosts)} product tiles on the page.")

                for i, host in enumerate(product_tile_hosts):
                    try:
                        if i%6 == 0:
                            # I sleep
                            time.sleep(random.uniform(0.05, 0.25))

                        name = host.find_element(By.CSS_SELECTOR, '.product__title').text.strip()
          
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
                return None

    unique_products = [
    json.loads(element) for element in set(
        json.dumps(data) for data in products_data
    )]
    
    print("Closing browser.")
    driver.quit()

    return unique_products

if __name__ == "__main__":
    print("Scraping Coles...")
    start_time = time.time()
    scraped_data = scrape_coles()
    
    if scraped_data and len(scraped_data) > 0:
        df = pd.DataFrame(scraped_data)
        file_name = 'coles_test_2.csv'
        df.to_csv(file_name, index=False, encoding='utf-8')
        print(f"\nScraping complete!") 
        print(f"Successfully scraped {len(scraped_data)} products.")
        print(f"Data saved to '{file_name}'")
        print("\n--- Sample of Scraped Data ---")
        print(df.head())
        print("Time taken:", str(time.time() - start_time))
    else:
        print("\nScraping failed. No data was retrieved.") 