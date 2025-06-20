import os
import pickle
import shutil
import logging
from time import sleep
from bs4 import BeautifulSoup
from xlsxwriter import Workbook
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InstagramScraper:
    def __init__(self, target_username, path, login_user=None, login_pass=None, login_method="direct", logger=None):
        self.target_username = target_username
        self.path = path
        self.login_user = login_user
        self.login_pass = login_pass
        self.login_method = login_method
        self.logger = logger or print  # ✅ Default to print if logger not passed
        self.error = False

    import requests

    def get_username_from_cookies(self):
        try:
            print("🌐 Extracting username using Instagram private API and cookies...")

            with open("instagram_cookies.pkl", "rb") as f:
                cookies_list = pickle.load(f)

            cookies = {c['name']: c['value'] for c in cookies_list}
            user_id = cookies.get("ds_user_id")
            sessionid = cookies.get("sessionid")

            if not user_id or not sessionid:
                print("❌ Required cookies not found.")
                return None

            headers = {
                "User-Agent": "Instagram 219.0.0.12.117 Android",
                "X-IG-App-ID": "936619743392459",  # public mobile app ID
            }

            response = requests.get(
                f"https://i.instagram.com/api/v1/users/{user_id}/info/",
                headers=headers,
                cookies={
                    "sessionid": sessionid,
                    "ds_user_id": user_id
                }
            )

            if response.status_code == 200:
                data = response.json()
                username = data["user"]["username"]
                print("✅ Instagram username resolved:", username)
                return username
            else:
                print(f"❌ Failed to get user info. Status code: {response.status_code}")
                print(response.text)
                return None

        except Exception as e:
            print("❌ Exception while resolving username:", e)
            return None



    def get_logged_in_username(self):
        try:
            print("🔍 Trying to extract username from profile icon link...")
            self.driver.get('https://www.instagram.com/')
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//nav")))

            sleep(3)

            # Find the profile link from nav bar — it contains username in href
            profile_link_elem = self.driver.find_element(By.XPATH, "//a[starts-with(@href, '/')]")
            href = profile_link_elem.get_attribute("href")

            print("🧪 Found profile link:", href)

            # Extract username from href like https://www.instagram.com/USERNAME/
            if href:
                username = href.strip('/').split('/')[-1]
                print("✅ Extracted username:", username)
                return username

            return None

        except Exception as e:
            print("❌ Could not extract username from profile link:", e)
            return None



    def login_and_scrape(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)

            self.driver.get('https://www.instagram.com/accounts/login/')
            self.perform_login()  # 🔐 Automated login

            if self.error:
                return

            self.save_cookies()

            self.open_target_profile()
            if not self.error:
                self.scroll_down()
            if not self.error:
                self.download_images()

        except Exception as e:
            logger.error(f"[Auto Login] Error during login and scrape: {e}")
            self.error = True
        finally:
            self.cleanup()


    def launch_browser_for_login(self):
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 120)

            print("🚀 Opening Instagram login...")
            self.driver.get('https://www.instagram.com/accounts/login/')
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//nav")))

            print("✅ Login successful. Saving cookies...")
            self.save_cookies()

            # ✅ Now use the new method to get real username
            actual_username = self.get_username_from_cookies()
            return actual_username

        except Exception as e:
            print("❌ Login error:", e)
            return None

        finally:
            self.cleanup()



    def scrape(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--headless')

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)

            self.driver.get('https://www.instagram.com/')
            self.load_cookies()
            self.driver.refresh()
            sleep(3)

            self.open_target_profile()
            if not self.error:
                self.scroll_down()
            if not self.error:
                self.download_images()

        except Exception as e:
            logger.error(f"Scrape failed: {e}")
            self.error = True
        finally:
            self.cleanup()




    def save_cookies(self):
        try:
            cookies = self.driver.get_cookies()
            with open("instagram_cookies.pkl", "wb") as f:
                pickle.dump(cookies, f)
        except Exception as e:
            logger.error(f"Cookie saving error: {e}")

    def load_cookies(self):
        try:
            with open("instagram_cookies.pkl", "rb") as f:
                cookies = pickle.load(f)
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            self.driver.refresh()
        except Exception as e:
            logger.error(f"Cookie loading error: {e}")

    def scroll_down(self):
        try:
            sleep(3)
            no_of_posts = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(),' posts')]"))
            ).text.split(' ')[0]
            no_of_posts = int(no_of_posts.replace(',', ''))
            no_of_scrolls = max(1, int(no_of_posts / 12) + 3)

            self.logger(f"🔃 Scrolling through {no_of_posts} posts...")

            for i in range(no_of_scrolls):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                sleep(2)

            sleep(5)

        except Exception as e:
            self.logger(f"❌ Scroll error: {e}")
            self.error = True


    def download_images(self):
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            self.all_images = soup.find_all('img')
            self.logger(f"📷 Found {len(self.all_images)} images")

            image_dir = os.path.join(self.path, 'images')
            description_path = os.path.join(self.path, 'descriptions')
            os.makedirs(image_dir, exist_ok=True)
            os.makedirs(description_path, exist_ok=True)

            for index, image in enumerate(self.all_images):
                try:
                    filename = f'image_{index}.jpg'
                    image_path = os.path.join(image_dir, filename)
                    link = image['src']

                    self.logger(f"📥 Downloading image {index + 1}/{len(self.all_images)}")
                    response = requests.get(link, stream=True)
                    response.raise_for_status()

                    with open(image_path, 'wb') as file:
                        shutil.copyfileobj(response.raw, file)

                    description = image.get('alt', 'No description available')
                    desc_filename = f'description_{index}.txt'
                    desc_path = os.path.join(description_path, desc_filename)

                    with open(desc_path, 'w', encoding='utf-8') as f:
                        f.write(f"Image: {filename}\nSource: {link}\nDescription: {description}")

                    sleep(1)
                except Exception as e:
                    self.logger(f"⚠️ Error processing image {index}: {e}")
                    continue

            self.create_excel_summary(description_path)

            excel_path = os.path.join(description_path, 'image_summary.xlsx')
            if os.path.exists(excel_path):
                self.logger(f"✅ Excel file created at: {excel_path}")
            else:
                self.logger("⚠️ Excel file not found after creation attempt")

        except Exception as e:
            self.logger(f"❌ Download error: {e}")
            self.error = True


    def create_excel_summary(self, description_path):
        try:
            workbook = Workbook(os.path.join(description_path, 'image_summary.xlsx'))
            worksheet = workbook.add_worksheet()

            headers = ['Image Name', 'Source URL', 'Description']
            for col, header in enumerate(headers):
                worksheet.write(0, col, header)

            for row, image in enumerate(self.all_images, start=1):
                worksheet.write(row, 0, f'image_{row-1}.jpg')
                worksheet.write(row, 1, image.get('src', 'N/A'))
                worksheet.write(row, 2, image.get('alt', 'No description'))

            workbook.close()
            logger.info("Excel summary created successfully")

        except Exception as e:
            logger.error(f"Excel creation error: {e}")

    def open_target_profile(self):
        try:
            profile_url = f'https://www.instagram.com/{self.target_username}/'
            self.driver.get(profile_url)
            sleep(5)

            if "Page Not Found" in self.driver.title or "Login" in self.driver.title:
                raise Exception("Profile not accessible or doesn't exist")

        except Exception as e:
            logger.error(f"Error accessing profile: {e}")
            self.error = True

    def cleanup(self):
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def perform_login(self):
        try:
            if self.login_method == 'facebook':
                fb_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Log in with Facebook')]")))
                fb_button.click()

                email_input = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
                pass_input = self.driver.find_element(By.ID, "pass")
                login_btn = self.driver.find_element(By.NAME, "login")

                email_input.send_keys(self.login_user)
                pass_input.send_keys(self.login_pass)
                login_btn.click()

                self.wait.until(EC.presence_of_element_located((By.XPATH, "//nav")))
                logger.info("Facebook login successful.")

            else:  # direct Instagram login
                username_input = self.wait.until(EC.presence_of_element_located((By.NAME, 'username')))
                password_input = self.driver.find_element(By.NAME, 'password')
                username_input.send_keys(self.login_user)
                password_input.send_keys(self.login_pass)

                login_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                login_btn.click()

                self.wait.until(EC.presence_of_element_located((By.XPATH, "//nav")))
                logger.info("Instagram login successful.")

        except Exception as e:
            logger.error(f"Login failed: {e}")
            self.error = True
    
    


