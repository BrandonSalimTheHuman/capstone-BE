import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, DetachedShadowRootException
import re
import random

URL = "https://www.woolworths.com.au"

def get_shadow_root(driver, host_element):
    return driver.execute_script('return arguments[0].shadowRoot', host_element)

def scrape_woolworths_specials():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    
    # options.add_argument('--headless')
    
    options.add_argument('--log-level=3')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window() 
    products_data = []
    
    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 10) # Use a 10-second wait for pop-ups

        # try:
        #     print("Looking for a location pop-up...")
        #     # Find the input field for postcode/suburb
        #     location_input = wait.until(EC.visibility_of_element_located((By.ID, 'wx-sl-search__input')))
        #     location_input.send_keys("Wollongong")
        #     time.sleep(1) 
        #     # Click the first search result
        #     first_result = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'mobile-search-result-item')))
        #     first_result.click()
        #     print("Successfully handled location pop-up.")
        #     time.sleep(3) 
        # except TimeoutException:
        #     print("No location pop-up found, continuing...")

        long_wait = WebDriverWait(driver, 10)
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
        while True:
            driver.get("https://www.woolworths.com.au/shop/browse/fruit-veg")
            try:
                long_wait = WebDriverWait(driver, 20)
                right_arrow_load = long_wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.chip-nav-arrow.right')))
                right_arrow = driver.find_element(By.CSS_SELECTOR, '.chip-nav-arrow.right')
                right_arrow.click()
                buttons_load = long_wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.chip.chip-secondary')))
                buttons = driver.find_elements(By.CSS_SELECTOR, '.chip.chip-secondary')
                for button in buttons:
                    time.sleep(0.5)
                    try:
                        button_text = button.find_element(By.CSS_SELECTOR, '.chip-text.ng-star-inserted')
                    except NoSuchElementException:
                        continue
                    if button_text.text.strip() == 'All filters':
                        button.click()
                break                   
            except StaleElementReferenceException: 
                print("Stale element encountered")
                print("Trying again")
            
        while True:
            try:
                long_wait = WebDriverWait(driver, 20)
                buttons_load = long_wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.checkbox-label.ng-star-inserted')))
                buttons = driver.find_elements(By.CSS_SELECTOR, '.checkbox-label.ng-star-inserted')
                for button in buttons:
                    time.sleep(0.5)
                    if button.text.strip() in ['In stock', 'Hide Everyday Market']:
                        button.click()
                confirm_button_load = long_wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.button.primary')))
                confirm_buttons = driver.find_elements(By.CSS_SELECTOR, '.button.primary')
                for button in confirm_buttons:
                    if button.text.strip() == 'See results':
                        button.click()
                        break
                break                   
            except StaleElementReferenceException: 
                print("Stale element encountered")
                print("Trying again")


        for category_url in category_urls:
            page_counter = 0
            newly_added_items = []
            while True:
                page_counter += 1
                driver.get(f'{URL}/shop/browse/{category_url}?pageNumber={page_counter}')
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
                                if len(complex_discount_words) == 3:
                                    for i in range(len(complex_discount_words)):
                                        if complex_discount_words[i] == 'for':
                                            complex_discount = {'Quantity': complex_discount_words[i-1], 'Price': complex_discount_words[i+1][1:]}
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
        print("Scraping failed: Timed out waiting for product tiles to appear.")
        print("Watch the browser window when the script runs to see what is blocking the content.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
    finally:
        print("Closing browser.")
        driver.quit()
        
    return products_data

if __name__ == "__main__":
    print("Scraping Woolworths test...")
    scraped_data = scrape_woolworths_specials()
    
    if scraped_data and len(scraped_data) > 0:
        df = pd.DataFrame(scraped_data)
        file_name = 'woolworths_test2.csv'
        df.to_csv(file_name, index=False, encoding='utf-8')
        print(f"\nScraping complete!") 
        print(f"Successfully scraped {len(scraped_data)} products.")
        print(f"Data saved to '{file_name}'")
        print("\n--- Sample of Scraped Data ---")
        print(df.head())
    else:
        print("\nScraping failed. No data was retrieved.") 