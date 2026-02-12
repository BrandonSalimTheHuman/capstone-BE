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

def scrape_iga():
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

    driver.get('https://www.igashop.com.au/')

    long_wait = WebDriverWait(driver, 7)
    location_field = long_wait.until(
        EC.presence_of_all_elements_located((By.ID, 'search-location'))
    )

    location_field = driver.find_element(By.ID, "search-location")
    location_field.send_keys("Mt Cotton")   

    long_wait = WebDriverWait(driver, 7)
    correct_location = long_wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-test-id="address-finder-result-1"]'))
    )

    correct_location = driver.find_element(By.CSS_SELECTOR, '[data-test-id="address-finder-result-1"]')
    correct_location.click()

    long_wait = WebDriverWait(driver, 7)
    store_id = long_wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-store-id="84971"]'))
    )

    select_button = driver.find_element(By.CSS_SELECTOR, '[data-store-id="84971"] button')

    select_button.click()


    long_wait = WebDriverWait(driver, 7)
    category_containers= long_wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-test-id^="category-navigation-item"]'))
    )

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
        long_wait = WebDriverWait(driver, 7)
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

    urls = ["https://www.igashop.com.au/categories/pantry/canned-food-and-instant-meals"]

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
                long_wait = WebDriverWait(driver, 20)
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
                        print(f"Name: {name}")
                        print(f"Price: {price}")
                        if len(key_text) > 4:
                            key_text[4] = key_text[4].text.replace("per", "")
                            unit_price = f"{key_text[3].text.strip()}/{key_text[4].strip()}"
                        elif len(key_text) > 3:
                            unit_price = key_text[3].text.strip()
                        else:
                            unit_price = "N/A"
                        print(f"Unit price: {unit_price}")
        
                        
                        img = host.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')

                        newly_added_items.append({'Product Name': name, 'Price': price, 'Unit Price': unit_price, 'Image': img})
    
                        print("Added one")
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
    print("Scraping IGA...")
    start_time = time.time()
    scraped_data = scrape_iga()
    
    if scraped_data and len(scraped_data) > 0:
        df = pd.DataFrame(scraped_data)
        file_name = 'iga_test.csv'
        df.to_csv(file_name, index=False, encoding='utf-8')
        print(f"\nScraping complete!") 
        print(f"Successfully scraped {len(scraped_data)} products.")
        print(f"Data saved to '{file_name}'")
        print("\n--- Sample of Scraped Data ---")
        print(df.head())
        print("Time taken:", str(time.time() - start_time))
    else:
        print("\nScraping failed. No data was retrieved.") 