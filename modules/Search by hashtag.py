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
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from datetime import datetime

class FacebookPageSearcher:
    def __init__(self):
        self.driver = self.setup_driver()

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run headless Chrome
        options.add_argument("--disable-popup-blocking")  # Disable popups
        options.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 2})

        driver = webdriver.Chrome(options=options)
        return driver

    def load_cookies(self, driver: webdriver.Chrome) -> bool:
        """Load cookies from the pickle file."""
        try:
            cookies_path = os.path.join(os.getcwd(), 'cookies.pkl')
            if not os.path.exists(cookies_path):
                self.create_and_save_cookies()
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

    def clean_facebook_url(self, url):
        # Parse the URL into components
        parsed_url = urlparse(url)
        # Extract query parameters
        query_params = parse_qs(parsed_url.query)

        # Keep only essential query parameters for Facebook profile links
        allowed_params = ['id']
        clean_query = {key: value for key, value in query_params.items() if key in allowed_params}

        # Rebuild the URL with the cleaned query string
        clean_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            None,  # Clear old query string
            urlencode(clean_query, doseq=True),
            None  # Fragment
        ))

        return clean_url

    def create_and_save_cookies(self):
        """Open browser, log in to Facebook, and save cookies to a file."""
        driver = self.setup_driver()
        driver.get('https://www.facebook.com')
        print("Please log in to Facebook and then press Enter...")
        input()  # Wait for user to log in and press Enter
        cookies = driver.get_cookies()  # Get cookies
        with open('cookies.pkl', 'wb') as file:
            pickle.dump(cookies, file)  # Save cookies to a file
        print("Cookies saved successfully!")
        driver.quit()  # Close the browser

    def search_pages(self, query: str, result_count: int = 10) -> List[dict]:
        """Search for Facebook pages with the given query."""
        try:
            if not self.load_cookies(self.driver):
                print("Failed to load cookies.")
                return []
            search_url = f"https://www.facebook.com/hashtag/{query}"
            print(f"Searching URL: {search_url}")
            self.driver.get(search_url)

            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            start_time = time.time()
            formatted_time = datetime.now().strftime("%H:%M:%S")
            collected_urls = []
            seen_links = set()
            total_pages = 0
            scroll_attempts = 0
            max_scroll_attempts = 10
            last_height = 0

            while len(seen_links) < result_count and scroll_attempts < max_scroll_attempts:
                try:
                    pages = self.driver.find_elements(By.XPATH, "//div[@role='article']")
                    total_pages = len(pages)
                    elapsed_time_minutes = (time.time() - start_time) / 60
                    print(f"\rFound {len(seen_links)} pages...  Analyzed {total_pages} posts...  Elapsed: {elapsed_time_minutes:.2f} minutes", end="", flush=True)

                    for page in pages:
                        if len(seen_links) >= result_count:
                            break
                        try:
                            link_element = page.find_element(By.CSS_SELECTOR,
                                                             "a.x1i10hfl.xjbqb8w.x1ejq31n.xd10rxx.x1sy0etr.x17r0tee.x972fbf.xcfux6l.x1qhh985.xm0m39n.x9f619.x1ypdohk.xt0psk2.xe8uvvx.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x16tdsg8.x1hl2dhg.xggy1nq.x1a2a7pz.x1sur9pj.xzsf02u.x1s688f")
                            page_link = link_element.get_attribute('href')
                            page_link = self.clean_facebook_url(page_link)
                            if page_link and page_link not in seen_links and '/groups/' not in page_link and '/events/' not in page_link and '/marketplace/' not in page_link and '/watch/' not in page_link and '/reels/' not in page_link and '/videos/' not in page_link and '/live/' not in page_link:
                                seen_links.add(page_link)
                                collected_urls.append(page_link)
                        except NoSuchElementException:
                            continue
                except StaleElementReferenceException:
                    print("\nStale element reference encountered, re-fetching elements...")
                    continue

                # Scroll and check for new content
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    scroll_attempts += 1
                    print(f"\nNo new content, attempt {scroll_attempts}/{max_scroll_attempts}")
                else:
                    scroll_attempts = 0
                    last_height = new_height

                # Check if we should stop scrolling
                if scroll_attempts >= max_scroll_attempts or len(seen_links) >= result_count:
                    print("\nScrolling stopped. Saving URLs and exiting...")
                    # Save the collected URLs before exiting
                    if collected_urls:
                        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                        formatted_query = query.replace(' ', '_')
                        filename = f'results/{formatted_query}_{result_count}_{current_time}.txt'
                        
                        # Ensure results directory exists
                        os.makedirs('results', exist_ok=True)
                        
                        # Save URLs to file
                        with open(filename, 'w', encoding='utf-8') as f:
                            for url in collected_urls:
                                f.write(url + '\n')
                        print(f"Saved {len(collected_urls)} URLs to {filename}")
                    break

            return [{'page_link': url} for url in collected_urls]
        finally:
            self.driver.quit()

    def save_urls_to_file(self, urls):
        # Generate a dynamic filename based on the search query, count, and current date/time
        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        formatted_query = "ثانويةعامة".replace(' ', '_')  # Replace spaces with underscores for filename
        filename = f'results/{formatted_query}_10_{current_time}.txt'

        # Save the URLs to file
        with open(filename, 'a', encoding='utf-8') as f:
            for url in urls:
                f.write(url + '\n')
        print(f"Saved URLs to {filename}")

    def measure_runtime(self, query: str, result_count: int = 10) -> List[dict]:
        start_time = time.time()  # Start timing
        results = self.search_pages(query, result_count)
        end_time = time.time()  # End timing
        runtime_minutes = (end_time - start_time) / 60  # Calculate runtime in minutes
        print(f"\nRuntime: {runtime_minutes:.2f} minutes")
        return results

if __name__ == "__main__":
    query = "ثانويةعامة"
    count = 100
    searcher = FacebookPageSearcher()
    results = searcher.measure_runtime(query, count)
    print("\nPage Links:")
    for result in results:
        print(result['page_link'])
