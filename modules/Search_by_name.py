import re
import os
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
from typing import List
from datetime import datetime

class FacebookPageSearcher:
    def __init__(self):
        self.driver = self.setup_driver()
        self.filepath = None  # Instance variable to store the file path
        self.folder_path = None  # Instance variable to store the folder path

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run headless Chrome
        options.add_argument("--disable-popup-blocking") 
        driver = webdriver.Chrome(options=options)
        return driver

    def load_cookies(self, driver: webdriver.Chrome) -> bool:
        """Load cookies from the pickle file."""
        try:
            cookies_path = os.path.join(os.getcwd(), 'data.pkl')
            if not os.path.exists(cookies_path):
                print(f"Cookie file not found at: {cookies_path}")
                return False
            driver.get("https://www.facebook.com")  # Navigate to Facebook to set cookies
            time.sleep(2)
            with open(cookies_path, 'rb') as file:
                cookies = pickle.load(file)
                for cookie in cookies:
                    driver.add_cookie(cookie)
            return True
        except Exception as e:
            print(f"Error loading cookies: {e}")
            return False

    def search_pages(self, autoscraping: bool, query: str, result_count: int = 10, log_callback=None) -> List[dict]:
        """Search for Facebook pages with the given query."""
        def log(message):
            if log_callback:
                log_callback(message)
            print(message)

        start_time = time.time()
        try:
            if not self.load_cookies(self.driver):
                log("Failed to load cookies.")
                return []
            search_url = f"https://www.facebook.com/search/pages/?q={query}"
            log(f"Initializing search at: {search_url}")
            self.driver.get(search_url)
            
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            results = []
            seen_links = set()
            total_pages = 0
            scroll_attempts = 0
            max_scroll_attempts = 20  # Increased from 10
            
            while len(seen_links) < result_count and scroll_attempts < max_scroll_attempts:
                try:
                    pages = self.driver.find_elements(By.XPATH, "//div[@role='article']")
                    total_pages = len(pages)
                    log(f"Progress: Found {len(seen_links)} pages | Analyzed {total_pages} posts | Elapsed: {(time.time() - start_time) / 60:.2f} minutes")
                    
                    for page in pages:
                        if len(seen_links) >= result_count:
                            break
                        try:
                            link_element = page.find_element(By.CSS_SELECTOR, 
                                "a.x1i10hfl.xjbqb8w.x1ejq31n.xd10rxx.x1sy0etr.x17r0tee.x972fbf.xcfux6l.x1qhh985.xm0m39n.x9f619.x1ypdohk.xt0psk2.xe8uvvx.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x16tdsg8.x1hl2dhg.xggy1nq.x1a2a7pz.x1sur9pj.xkrqix3.xzsf02u.x1pd3egz")
                            page_link = link_element.get_attribute('href')
                            if page_link and page_link not in seen_links:
                                seen_links.add(page_link)
                                results.append({'page_link': page_link})
                        except NoSuchElementException:
                            continue
                except StaleElementReferenceException:
                    log("Stale element reference encountered, re-fetching elements...")
                    continue
                
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Wait for new content to load
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == total_pages:
                    scroll_attempts += 1
                    log(f"No new content found, attempt {scroll_attempts}/{max_scroll_attempts}")
                else:
                    scroll_attempts = 0
                
            log(f"Search complete! Total pages analyzed: {total_pages}")
            
            # Generate filename with current date and time
            log("Saving results to file...")
            current_datetime = datetime.now()
            date_str = current_datetime.strftime("%Y-%m-%d")
            time_str = current_datetime.strftime("%H-%M-%S")
            if autoscraping:
                self.folder_path = f"results/{query}&{result_count}&{date_str}&{time_str}"
                os.makedirs(self.folder_path, exist_ok=True)
                self.filepath = f"{self.folder_path}/{query}&{result_count}&{date_str}&{time_str}.txt"
            else:
                self.filepath = f"results/{query}&{result_count}&{date_str}&{time_str}.txt"
            
            with open(self.filepath, 'w', encoding='utf-8') as f:
                for result in results:
                    f.write(result['page_link'] + '\n')
                
            return results
        finally:
            self.driver.quit()

if __name__ == "__main__":
    start_time = time.time()  # Start timing
    query = "مستر"
    count = 100
    searcher = FacebookPageSearcher()
    results = searcher.search_pages(query, count)
    print("\nPage Links:")
    for result in results:
        print(result['page_link'])
    end_time = time.time()  # End timing
    runtime_minutes = (end_time - start_time) / 60  # Calculate runtime in minutes
    print(f"\nRuntime: {runtime_minutes:.2f} minutes")
