import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import json

URL = "https://www.aldi.com.au/products"

# def get_shadow_root(driver, host_element):
#     return driver.execute_script('return arguments[0].shadowRoot', host_element)

def scrape_aldi_specials():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    
    # options.add_argument('--headless')
    
    options.add_argument('--log-level=3')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window() 

    products_data = []
    page_counter = 0

    while True:
        try:
            page_counter += 1
            driver.get(f'{URL}?page={page_counter}')

            print("Waiting for product tiles to load...")
            long_wait = WebDriverWait(driver, 7)
            product_tile_hosts = long_wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.product-tile__link'))
            )
                
            print(f"Found {len(product_tile_hosts)} product tiles on the page.")

            for host in product_tile_hosts:
                try:
                    # shadow_root = get_shadow_root(driver, host)
                    name = host.find_element(By.CSS_SELECTOR, '.product-tile__name').text.strip()
                    price = host.find_element(By.CSS_SELECTOR, '.base-price__regular').text.strip()
                                
                    try:
                        unit_price = host.find_element(By.CSS_SELECTOR, '.base-price__comparison-price').text.strip()[1:-1]
                    except NoSuchElementException:
                        unit_price = "N/A"

                    img = host.find_element(By.CSS_SELECTOR, '.base-image').get_attribute('src')

                    products_data.append({'Product Name': name, 'Price': price, 'Unit Price': unit_price, "Image url": img})
                    
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
    print("Scraping Aldi...")
    scraped_data = scrape_aldi_specials()
    print(scraped_data)
    if scraped_data and len(scraped_data) > 0:
        df = pd.DataFrame(scraped_data)
        file_name = 'aldi_cheese_test.csv'
        df.to_csv(file_name, index=False, encoding='utf-8')
        print(f"\nScraping complete!") 
        print(f"Successfully scraped {len(scraped_data)} products.")
        print(f"Data saved to '{file_name}'")
        print("\n--- Sample of Scraped Data ---")
        print(df.head())
    else:
        print("\nScraping failed. No data was retrieved.") 