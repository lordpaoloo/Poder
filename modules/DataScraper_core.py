import gc
import os
import pickle
import re
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import pandas as pd
import unicodedata

class FacebookScraper:
	# Contact Information
	CONTACT_PHONE = "+201550838674"
	CONTACT_EMAIL = "youssef.mohamad.abdallah@gmail.com"

	def __init__(self, callback=None):
		"""Initialize the WebDriver with headless options."""
		self.driver = self.initialize_webdriver()
		self.callback = callback  # Callback function for logging
		self.is_running = False

	def log(self, message):
		"""Log messages through callback if provided"""
		if self.callback:
			self.callback(message)
		else:
			print(message)

	def initialize_webdriver(self):
		"""Initialize the Selenium WebDriver with options."""
		options = Options()
		options.add_argument('--headless=new')
		options.add_argument('--disable-gpu')
		options.add_argument('--no-sandbox')
		options.add_argument('--disable-dev-shm-usage')
		options.add_argument('--disable-software-rasterizer')
		options.add_argument('--disable-extensions')
		options.add_argument('--disable-logging')
		options.add_argument('--disable-application-cache')
		options.add_argument('--ignore-certificate-errors')
		options.add_argument('--disable-popup-blocking')
		options.add_argument('--window-size=1920,1080')
		options.add_argument('--disable-blink-features=AutomationControlled')
		options.add_experimental_option('excludeSwitches', ['enable-automation'])
		options.add_experimental_option('useAutomationExtension', False)
		options.page_load_strategy = 'normal'

		driver = webdriver.Chrome(options=options)
		time.sleep(3)
		return driver

	def start_scraping(self, urls):
		"""Start the scraping process"""
		self.is_running = True
		try:
			self.load_cookies_from_file()
			results = self.extract_data_from_urls(urls)
			return results
		finally:
			self.is_running = False
			self.driver.quit()

	def stop_scraping(self):
		"""Stop the scraping process"""
		self.is_running = False
		self.log("Stopping scraping process...")

	def load_cookies_from_file(self, file_path=None):
		if file_path is None:
			file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies.pkl')

		try:
			with open(file_path, 'rb') as file:
				cookies = pickle.load(file)
				self.driver.get('https://www.facebook.com')
				for cookie in cookies:
					if 'domain' not in cookie or not cookie['domain']:
						cookie['domain'] = '.facebook.com'
					try:
						if 'expiry' in cookie:
							del cookie['expiry']
						self.driver.add_cookie(cookie)
					except Exception as e:
						self.log(f"Error adding cookie: {e}")
		except FileNotFoundError:
			self.log("Cookies file not found.")
		except Exception as e:
			self.log(f"Error loading cookies: {e}")

	def clean_facebook_url(self, url):
		"""Clean Facebook URLs while preserving profile IDs."""
		if not url:
			return url

		if 'profile.php?id=' in url:
			match = re.search(r'profile\.php\?id=(\d+)', url)
			if match:
				return f'https://www.facebook.com/profile.php?id={match.group(1)}'

		return url.split('?')[0].rstrip('/')

	def extract_followers_data(self, profile_url):
		"""Extract follower count, phone number, and email from a Facebook profile."""
		if not self.is_running:
			return None, None, None, []

		if '/groups/' in profile_url:
			self.log("Groups are not supported.")
			return None, None, None, []

		profile_url = self.clean_facebook_url(profile_url)
		self.log(f"Visiting profile: {profile_url}")

		try:
			self.driver.get(profile_url)
			WebDriverWait(self.driver, 10).until(
				EC.presence_of_element_located((By.TAG_NAME, 'body'))
			)

			self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
			time.sleep(5)

			links = self.extract_links()
			html = self.driver.page_source
			soup = BeautifulSoup(html, 'html.parser')

			followers_count = self.get_followers_count(soup)
			email = self.get_email()
			phone_number = self.get_phone_number()

			return followers_count, phone_number, email, links

		except Exception as e:
			self.log(f"Error extracting data: {e}")
			return None, None, None, []

	def extract_links(self):
		"""Extract links from profile."""
		try:
			class_name = 'x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x xudqn12 x3x7a5m x6prxxf xvq8zen xo1l8bm x1fey0fg'
			span_elements = self.driver.find_elements(By.XPATH, f"//span[contains(@class, '{class_name}')]")
			return [span.text.strip() for span in span_elements if span.text.strip()]
		except Exception as e:
			self.log(f"Error extracting text from spans: {e}")
			return []

	def get_followers_count(self, soup):
		"""Extract follower count from the pro page."""
		try:
			followers_elements = soup.find_all('a', href=True)
			for element in followers_elements:
				text = element.get_text(strip=True)
				if "follower" in text.lower():
					return self.convert_follower_count(text)
			return None
		except Exception as e:
			self.log(f"Error extracting followers: {e}")
			return None

	def convert_follower_count(self, follower_str):
		"""Convert follower count string to an integer."""
		try:
			cleaned = ''.join(c for c in follower_str if c.isdigit() or c in 'KMk.m').lower()
			if 'k' in cleaned:
				return int(float(cleaned.replace('k', '')) * 1000)
			elif 'm' in cleaned:
				return int(float(cleaned.replace('m', '')) * 1000000)
			return int(float(cleaned))
		except ValueError as e:
			self.log(f"Error converting follower count: {e}")
			return 0

	def get_email(self):
		"""Extract email from the page source."""
		try:
			html_content = self.driver.page_source
			email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', html_content)
			return email_match.group() if email_match else None
		except Exception as e:
			self.log(f"Error extracting email address: {e}")
			return None

	def get_phone_number(self):
		"""Extract phone number from span elements using XPath."""
		try:
			class_name = 'x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x xudqn12 x3x7a5m x6prxxf xvq8zen xo1l8bm xzsf02u x1yc453h'
			phone_elements = self.driver.find_elements(By.XPATH, f"//span[contains(@class, '{class_name}')]")
			phone_pattern = re.compile(r"\b(\d{2,3})?[\s\.-]?\d{2,4}[\s\.-]?\d{3,4}[\s\.-]?\d{3,4}\b")
			for element in phone_elements:
				phone_match = phone_pattern.search(element.text.strip())
				if phone_match:
					phone_number = phone_match.group().replace("-", "").replace(".", "").replace(" ", "")
					if len(phone_number) >= 10:
						return phone_number
			return None
		except Exception as e:
			self.log(f"Error extracting phone number: {e}")
			return None

	def extract_data_from_urls(self, urls):
		"""Extract data from multiple Facebook profile URLs."""
		results = []
		for url in urls:
			if not self.is_running:
				break
				
			try:
				followers_count, phone_number, email, profile_links = self.extract_followers_data(url)
				page_name = self.get_page_name(url)
				result = {
					'url': url,
					'name': page_name,
					'followers_count': followers_count,
					'phone_number': phone_number,
					'email': email,
					'profile_links': ', '.join(profile_links) if profile_links else ''
				}
				results.append(result)
				self.save_to_excel(result)
				self.log(f"Successfully processed URL: {url}")
			except Exception as e:
				self.log(f"Error processing URL {url}: {e}")
				results.append({'url': url, 'error': str(e)})
			gc.collect()
		return results

	def save_to_excel(self, data, filename='scraped_data.xlsx'):
		"""Save scraped data to an Excel file."""
		try:
			if isinstance(data, list):
				new_df = pd.DataFrame(data)
			else:
				new_df = pd.DataFrame([data])

			if os.path.exists(filename):
				try:
					existing_df = pd.read_excel(filename)
					combined_df = pd.concat([existing_df, new_df], ignore_index=True)
				except Exception as e:
					self.log(f"Error reading existing Excel file: {e}")
					combined_df = new_df
			else:
				combined_df = new_df

			combined_df.drop_duplicates(subset=['url'], keep='last', inplace=True)

			if 'name' in combined_df.columns:
				combined_df['name'] = combined_df['name'].apply(lambda x: 
					unicodedata.normalize('NFKC', str(x)) if pd.notnull(x) else x)

			combined_df.to_excel(filename, index=False, engine='openpyxl')
			self.log(f"Data saved to {filename}")
		except Exception as e:
			self.log(f"Error saving to Excel: {e}")