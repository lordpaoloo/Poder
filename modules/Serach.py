import sys
import time
import re
import pickle
import os
import gc
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class FacebookSearchScraper:
    """Handles Facebook hashtag search functionality."""
    
    def __init__(self):
        self.base_url = "https://www.facebook.com/hashtag/"
        self.driver = None
        
    def dismiss_notification_popup(self, driver: webdriver.Chrome) -> None:
        """Attempt to dismiss any notification popups that might appear."""
        try:
            notification_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@title='Allow all cookies']"))
            )
            notification_button.click()
        except Exception:
            pass

    def setup_driver(self) -> webdriver.Chrome:
        """Configure and return a Chrome WebDriver instance."""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--lang=ar')  # Set language to Arabic
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--enable-javascript')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        # Set user agent
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        return driver
        
    def load_cookies(self, driver: webdriver.Chrome, cookies_file='cookies.pkl') -> bool:
        """Load cookies from the pickle file."""
        try:
            # First navigate to Facebook domain to set cookies
            driver.get("https://www.facebook.com")
            time.sleep(2)
            
            # Load cookies from file
            if os.path.exists(cookies_file):
                with open(cookies_file, 'rb') as file:
                    cookies = pickle.load(file)
                    for cookie in cookies:
                        driver.add_cookie(cookie)
                return True
            return False
        except Exception as e:
            print(f"Error loading cookies: {e}")
            return False
            
    def search_hashtag(self, hashtag: str, result_count: int = 10) -> List[dict]:
        """
        Search for posts with a specific hashtag on Facebook.
        
        Args:
            hashtag: The hashtag to search for (without the # symbol)
            result_count: Number of results to retrieve
            
        Returns:
            List of dictionaries containing post information
        """
        start_time = time.time()
        try:
            driver = self.setup_driver()
            
            # Load cookies
            if not self.load_cookies(driver):
                print("Failed to load cookies. Make sure cookies.pkl exists.")
                return []
                
            # Navigate to hashtag search
            search_url = f"{self.base_url}{hashtag}"
            print(f"Searching URL: {search_url}")
            driver.get(search_url)
            
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                pass
                
            self.dismiss_notification_popup(driver)
            
            try:
                WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@role='article']"))
                )
            except TimeoutException:
                print("No posts found within the timeout period.")
                return []
            
            results = []
            last_height = driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scroll_attempts = 10
            seen_links = set()  # Track unique links
            total_posts_checked = 0
            
            while len(seen_links) < result_count and scroll_attempts < max_scroll_attempts:
                try:
                    posts = driver.find_elements(By.XPATH, "//div[@role='article']")
                    total_posts_checked = len(posts)
                    print(f"\rAnalyzed {total_posts_checked} posts, Found {len(seen_links)} unique profiles...", end="", flush=True)
                    
                    for post in posts:
                        if len(seen_links) >= result_count:
                            break
                            
                        try:
                            post_data = self._extract_post_info(post)
                            if post_data and post_data['author_link'] not in seen_links:
                                seen_links.add(post_data['author_link'])
                                results.append(post_data)
                                
                        except NoSuchElementException:
                            continue
                    
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    try:
                        WebDriverWait(driver, 2).until(
                            lambda d: d.execute_script("return document.body.scrollHeight") > last_height
                        )
                    except TimeoutException:
                        pass
                    
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        scroll_attempts += 1
                        print(f"\nNo new content, attempt {scroll_attempts}/{max_scroll_attempts}")
                    else:
                        scroll_attempts = 0
                    last_height = new_height
                    
                except Exception as e:
                    print(f"\nError while scraping: {e}")
                    break
                    
            runtime = time.time() - start_time
            print(f"\nScraping Summary:")
            print(f"Total posts analyzed: {total_posts_checked}")
            print(f"Unique profiles found: {len(seen_links)}")
            print(f"Time taken: {runtime:.2f} seconds")
            return results
            
        finally:
            if driver:
                driver.quit()
                
    def _clean_profile_url(self, url: str) -> str:
        """Clean Facebook profile URL by removing tracking parameters."""
        if not url:
            return url
        # Remove everything after '&__cft__' or '&__tn__'
        url = url.split('&__cft__')[0]
        url = url.split('&__tn__')[0]
        return url

    def _extract_post_info(self, post_element) -> Optional[dict]:
        """Extract author profile link from a post element."""
        try:
            author_element = post_element.find_element(By.XPATH, ".//a[@role='link'][contains(@href, '/')]")
            author_link = author_element.get_attribute('href')
            if author_link and ('/profile.php?id=' in author_link or '/people/' in author_link):
                clean_link = self._clean_profile_url(author_link)
                return {
                    'author_link': clean_link
                }
            return None
        except NoSuchElementException:
            return None

def search_facebook_hashtag(hashtag: str, count: int = 10) -> List[dict]:
    """
    Utility function to perform a hashtag search.
    
    Args:
        hashtag: Hashtag to search for (without # symbol)
        count: Number of results to retrieve
        
    Returns:
        List of scraped posts
    """
    scraper = FacebookSearchScraper()
    return scraper.search_hashtag(hashtag, count)

if __name__ == "__main__":
    hashtag = input("Enter hashtag to search (without #): ")
    count = int(input("Enter number of results to retrieve: "))
    
    results = search_facebook_hashtag(hashtag, count)
    print(f"\nFound {len(results)} posts:")
    for idx, post in enumerate(results, 1):
        print(f"\nPost {idx}:")
        print(f"Author Link: {post['author_link']}")