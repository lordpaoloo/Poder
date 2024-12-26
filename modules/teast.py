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
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtWidgets import (
    QApplication, QDialog, QProgressBar,
    QVBoxLayout, QPushButton, QTextEdit,
    QFrame, QLabel, QRadioButton, 
    QButtonGroup, QFileDialog, QMessageBox,
    QScrollArea, QWidget
)
import pandas as pd
import unicodedata

class FacebookScraper:
    # Contact Information
    CONTACT_PHONE = "+201550838674"
    CONTACT_EMAIL = "youssef.mohamad.abdallah@gmail.com"

    def __init__(self):
        """Initialize the WebDriver with headless options."""
        self.driver = self.initialize_webdriver()

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

    def load_cookies_from_file(self, file_path=None):
        if file_path is None:
            # Set the default path to be within the application directory
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
                        print(f"Error adding cookie: {e}")
        except FileNotFoundError:
            print("Cookies file not found.")
        except Exception as e:
            print(f"Error loading cookies: {e}")

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
        if '/groups/' in profile_url:
            print("Groups are not supported.")
            return None, None, None, []

        profile_url = self.clean_facebook_url(profile_url)
        print(f"Visiting profile: {profile_url}")

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
            print(f"Error extracting data: {e}")
            return None, None, None, []

    def extract_links(self):
        """Extract links from profile."""
        try:
            class_name = 'x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x xudqn12 x3x7a5m x6prxxf xvq8zen xo1l8bm x1fey0fg x1yc453h'
            span_elements = self.driver.find_elements(By.XPATH, f"//span[contains(@class, '{class_name}')]")
            return [span.text.strip() for span in span_elements if span.text.strip()]
        except Exception as e:
            print(f"Error extracting text from spans: {e}")
            return []

    def get_followers_count(self, soup):
        """Extract follower count from the profile page."""
        try:
            followers_elements = soup.find_all('a', href=True)
            for element in followers_elements:
                text = element.get_text(strip=True)
                if "follower" in text.lower():
                    return self.convert_follower_count(text)
            return None
        except Exception as e:
            print(f"Error extracting followers: {e}")
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
            print(f"Error converting follower count: {e}")
            return 0

    def get_email(self):
        """Extract email from the page source."""
        try:
            html_content = self.driver.page_source
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', html_content)
            return email_match.group() if email_match else None
        except Exception as e:
            print(f"Error extracting email address: {e}")
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
            print(f"Error extracting phone number: {e}")
            return None

    def get_page_name(self, url):
        """Get the name of the Facebook page."""
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Class name for the page name element
            class_name = 'html-h1 xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1vvkbs x1heor9g x1qlqyl8 x1pd3egz x1a2a7pz'
            name_elements = self.driver.find_elements(By.XPATH, f"//h1[contains(@class, '{class_name}')]")
            
            # Get the first non-empty name element
            for element in name_elements:
                name = element.text.strip()
                if name:
                    # Convert to bytes and decode as UTF-8
                    try:
                        # Try to normalize the Arabic text
                        normalized_name = unicodedata.normalize('NFKC', name)
                        return normalized_name
                    except:
                        return name
            return None
        except Exception as e:
            print(f"Error getting page name: {e}")
            return None

    def save_to_excel(self, data, filename='scraped_data.xlsx'):
        """Save scraped data to an Excel file."""
        try:
            # Convert data to DataFrame
            if isinstance(data, list):
                new_df = pd.DataFrame(data)
            else:
                new_df = pd.DataFrame([data])

            # Read existing Excel file if it exists
            if os.path.exists(filename):
                try:
                    existing_df = pd.read_excel(filename)
                    # Concatenate new data with existing data
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                except Exception as e:
                    print(f"Error reading existing Excel file: {e}")
                    combined_df = new_df
            else:
                combined_df = new_df

            # Remove duplicates based on URL
            combined_df.drop_duplicates(subset=['url'], keep='last', inplace=True)

            # Normalize Arabic text in the name column
            if 'name' in combined_df.columns:
                combined_df['name'] = combined_df['name'].apply(lambda x: 
                    unicodedata.normalize('NFKC', str(x)) if pd.notnull(x) else x)

            # Save to Excel with proper encoding
            combined_df.to_excel(filename, index=False, engine='openpyxl')
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving to Excel: {e}")

    def extract_data_from_urls(self, urls):
        """Extract data from multiple Facebook profile URLs."""
        results = []
        for url in urls:
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
                # Save each result to Excel
                self.save_to_excel(result)
                print(f"Successfully processed URL: {url}")
            except Exception as e:
                print(f"Error processing URL {url}: {e}")
                results.append({'url': url, 'error': str(e)})
            gc.collect()
        return results

class ScraperWorker(QThread):
    """Worker thread for running the scraper"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(list)
    
    def __init__(self, scraper, file_path=None):
        super().__init__()
        self.scraper = scraper
        self.file_path = file_path

    def run(self):
        try:
            self.status.emit("Loading cookies...")
            self.scraper.load_cookies_from_file()

            # Load URLs from file or database
            if isinstance(self.file_path, list):
                urls = self.file_path
            else:
                self.status.emit(f"Loading URLs from file: {self.file_path}")
                urls = self.load_urls_from_file(self.file_path)

            if not urls:
                self.status.emit("No URLs found")
                return

            total_urls = len(urls)

            for i, url in enumerate(urls, 1):
                try:
                    self.status.emit(f"Processing {i}/{total_urls}: {url}")
                    result = self.scraper.extract_data_from_urls([url])[0]

                    if result['followers_count'] is not None:
                        # Save each result to Excel
                        self.scraper.save_to_excel(result)
                        self.status.emit(f"Successfully processed URL: {url}")
                    else:
                        self.status.emit(f"Failed to extract data for URL: {url}")

                    progress = int((i / total_urls) * 100)
                    self.progress.emit(progress)

                except Exception as e:
                    self.status.emit(f"Error processing URL {url}: {e}")
                    continue

            self.finished.emit([])

        except Exception as e:
            self.status.emit(f"Error during scraping: {e}")
        finally:
            self.scraper.driver.quit()

    def load_urls_from_file(self, file_path):
        """Load URLs from a specified file."""
        try:
            with open(file_path, 'r') as file:
                urls = [line.strip() for line in file if line.strip()]
            return urls
        except Exception as e:
            print(f"Error loading URLs from file: {e}")
            return []

class ScraperGUI(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set modal and prevent interaction with parent
        self.setModal(True)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        
        self.initUI()
        
    def initUI(self):
        # Set window properties
        self.setWindowTitle('Facebook Profile Scraper')
        self.setMinimumSize(600, 400)
        
        # Create central widget and layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Style
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QProgressBar {
                border: 2px solid #2196F3;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QLabel {
                font-size: 14px;
            }
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
            QLabel.contact-info {
                color: #666666;
                font-size: 10pt;
                padding: 2px;
            }
        """)
        
        # Add title label
        title_label = QLabel('Facebook Profile Scraper')
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(title_label)
        
        # Add radio buttons for source selection
        self.file_radio = QRadioButton("Scrape from file")
        self.db_radio = QRadioButton("Scrape from database")
        self.db_radio.setChecked(True)
        
        self.radio_group = QButtonGroup()
        self.radio_group.addButton(self.file_radio)
        self.radio_group.addButton(self.db_radio)
        
        layout.addWidget(self.file_radio)
        layout.addWidget(self.db_radio)

        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Add start button
        self.start_button = QPushButton("Start Scraping")
        self.start_button.clicked.connect(self.start_scraping)
        layout.addWidget(self.start_button)

        # Add text area for displaying results
        self.results_area = QTextEdit()
        self.results_area.setReadOnly(True)
        layout.addWidget(self.results_area)

        # Add contact information at the bottom
        contact_frame = QFrame()
        contact_frame.setStyleSheet("QFrame { border-top: 1px solid #cccccc; margin-top: 10px; }")
        contact_layout = QVBoxLayout(contact_frame)
        
        contact_phone = QLabel(f"Contact Phone: {FacebookScraper.CONTACT_PHONE}")
        contact_email = QLabel(f"Contact Email: {FacebookScraper.CONTACT_EMAIL}")
        contact_phone.setProperty("class", "contact-info")
        contact_email.setProperty("class", "contact-info")
        
        contact_layout.addWidget(contact_phone)
        contact_layout.addWidget(contact_email)
        contact_layout.setSpacing(5)
        contact_layout.setContentsMargins(0, 10, 0, 0)
        
        layout.addWidget(contact_frame)

    def start_scraping(self):
        source = 'file' if self.file_radio.isChecked() else 'database'
        file_path = None
        
        # If file source is selected, prompt for file selection
        if source == 'file':
            options = QFileDialog.Options()
            options |= QFileDialog.ReadOnly
            file_path, _ = QFileDialog.getOpenFileName(self, "Select URL File", "", "Text Files (*.txt);;All Files (*)", options=options)
            if not file_path:
                self.update_status("File selection cancelled.")
                return
        elif source == 'database':
            urls = get_urls_missing_data()
            if not urls:
                self.update_status("No URLs found with missing data.")
                return
            file_path = urls

        # Initialize worker
        self.worker = ScraperWorker(FacebookScraper(), file_path)
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.display_results)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, status):
        self.results_area.append(status + '\n')

    def display_results(self, results):
        """Display the scraping results in the text area."""
        self.results_area.clear()
        for result in results:
            self.results_area.append(f"URL: {result['url']}")
            self.results_area.append(f"Name: {result.get('name', 'N/A')}")
            self.results_area.append(f"Followers: {result.get('followers_count', 'N/A')}")
            self.results_area.append(f"Phone: {result.get('phone_number', 'N/A')}")
            self.results_area.append(f"Email: {result.get('email', 'N/A')}")
            self.results_area.append(f"Profile Links: {result.get('profile_links', 'N/A')}")
            self.results_area.append("-" * 50)  # Add a separator line

        # Show a message box when the scraping is finished
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText("Scraping Finished")
        msg_box.setInformativeText("The scraping process has completed successfully.")
        msg_box.setWindowTitle("Finished")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

def get_urls_missing_data():
    # This function is not used anymore since database storage is replaced with Excel
    pass

# Update the main block to use QDialog
if __name__ == "__main__":
    app = QApplication([])
    gui = ScraperGUI()
    gui.show()
    app.exec_()
