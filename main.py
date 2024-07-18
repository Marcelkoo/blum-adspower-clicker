import requests
import os
import time
import logging
import json
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s')

class BrowserManager:
    def __init__(self, serial_number):
        self.serial_number = serial_number
        self.driver = None
    
    def check_browser_status(self):
        try:
            response = requests.get(
                'http://local.adspower.net:50325/api/v1/browser/active',
                params={'serial_number': self.serial_number}
            )
            data = response.json()
            if data['code'] == 0 and data['data']['status'] == 'Active':
                logging.info(f"Account {self.serial_number}: Browser is already active.")
                return True
            else:
                return False
        except Exception as e:
            logging.exception(f"Account {self.serial_number}: Exception in checking browser status: {str(e)}")
            return False

    def start_browser(self):
        try:
            if self.check_browser_status():
                logging.info(f"Account {self.serial_number}: Browser already open. Closing the existing browser.")
                self.close_browser()
                time.sleep(5)

            script_dir = os.path.dirname(os.path.abspath(__file__))
            requestly_extension_path = os.path.join(script_dir, 'blum_unlocker_extension')

            launch_args = json.dumps(["--headless=new", f"--load-extension={requestly_extension_path}"])

            request_url = (
                f'http://local.adspower.net:50325/api/v1/browser/start?'
                f'serial_number={self.serial_number}&ip_tab=1&headless=1&launch_args={launch_args}'
            )

            response = requests.get(request_url)
            data = response.json()
            if data['code'] == 0:
                selenium_address = data['data']['ws']['selenium']
                webdriver_path = data['data']['webdriver']
                chrome_options = Options()
                chrome_options.add_experimental_option("debuggerAddress", selenium_address)

                service = Service(executable_path=webdriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.set_window_size(600, 720)
                logging.info(f"Account {self.serial_number}: Browser started successfully.")
                return True
            else:
                logging.warning(f"Account {self.serial_number}: Failed to start the browser. Error: {data['msg']}")
                return False
        except Exception as e:
            logging.exception(f"Account {self.serial_number}: Exception in starting browser: {str(e)}")
            return False

    def close_browser(self):
        try:
            if self.driver:
                try:
                    self.driver.close()
                    self.driver.quit()
                    self.driver = None  
                    logging.info(f"Account {self.serial_number}: Browser closed successfully.")
                except WebDriverException as e:
                    logging.info(f"Account {self.serial_number}: exception, Browser should be closed now")
        except Exception as e:
            logging.exception(f"Account {self.serial_number}: General Exception occurred when trying to close the browser: {str(e)}")
        finally:
            try:
                response = requests.get(
                    'http://local.adspower.net:50325/api/v1/browser/stop',
                    params={'serial_number': self.serial_number}
                )
                data = response.json()
                if data['code'] == 0:
                    logging.info(f"Account {self.serial_number}: Browser closed successfully.")
                else:
                    logging.info(f"Account {self.serial_number}: exception, Browser should be closed now")
            except Exception as e:
                logging.exception(f"Account {self.serial_number}: Exception occurred when trying to close the browser: {str(e)}")

class TelegramBotAutomation:
    def __init__(self, serial_number):
        self.serial_number = serial_number
        self.browser_manager = BrowserManager(serial_number)
        logging.info(f"Initializing automation for account {serial_number}")
        self.browser_manager.start_browser()
        self.driver = self.browser_manager.driver

    def navigate_to_bot(self):
        try:
            self.driver.get('https://web.telegram.org/k/')
            logging.info(f"Account {self.serial_number}: Navigated to Telegram web.")
        except Exception as e:
            logging.exception(f"Account {self.serial_number}: Exception in navigating to Telegram bot: {str(e)}")
            self.browser_manager.close_browser()

    def send_message(self, message):
        chat_input_area = self.wait_for_element(By.XPATH, '/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/input[1]')
        chat_input_area.click()
        chat_input_area.send_keys(message)

        search_area = self.wait_for_element(By.XPATH, '/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[3]/div[2]/div[2]/div[2]/div[1]/div[1]/div[1]/div[2]/ul[1]/a[1]/div[1]')
        search_area.click()
        logging.info(f"Account {self.serial_number}: Group searched.")

    def click_link(self):
        link = self.wait_for_element(By.CSS_SELECTOR, "a[href*='t.me/BlumCryptoBot/app?startapp']")
        link.click()

        launch_click = self.wait_for_element(By.XPATH, "//body/div[@class='popup popup-peer popup-confirmation active']/div[@class='popup-container z-depth-1']/div[@class='popup-buttons']/button[1]/div[1]")
        launch_click.click()
        logging.info(f"Account {self.serial_number}: BLUM STARTED")
        sleep_time = random.randint(20, 30)
        logging.info(f"Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)
        if not self.switch_to_iframe():
            logging.info(f"Account {self.serial_number}: No iframes found")
            return

        try:
            daily_reward_button = WebDriverWait(self.driver, 1).until(
                EC.element_to_be_clickable((By.XPATH, "/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[2]/div[3]/button[1]"))
            )
            daily_reward_button.click()
            logging.info(f"Account {self.serial_number}: Daily reward claimed.")
            time.sleep(2)
        except TimeoutException:
            logging.info(f"Account {self.serial_number}: Daily reward has already been claimed or button not found.")

    def check_claim_button(self):
        if not self.switch_to_iframe():
            logging.info(f"Account {self.serial_number}: No iframes found")
            return
        
        initial_balance = self.check_balance()
        self.process_buttons()
        final_balance = self.check_balance()

        if final_balance is not None and initial_balance == final_balance and not self.is_farming_active():
            raise Exception(f"Account {self.serial_number}: Balance did not change after claiming tokens.")

    def switch_to_iframe(self):
        self.driver.switch_to.default_content()
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            self.driver.switch_to.frame(iframes[0])
            return True
        return False

    def process_buttons(self):
        buttons = self.wait_for_elements(By.CSS_SELECTOR, "div.index-farming-button")
        logging.info(f"Account {self.serial_number}: Found {len(buttons)} buttons")
        for button in buttons:
            self.process_single_button(button)

    def process_single_button(self, button):
        button_text = self.get_button_text(button)
        amount_elements = button.find_elements(By.CSS_SELECTOR, "div.amount")
        amount_text = amount_elements[0].text if amount_elements else None

        if "Farming" in button_text:
            self.handle_farming(button)
        elif "Start farming" in button_text and not amount_text:
            self.start_farming(button)
        elif amount_text:
            self.claim_tokens(button, amount_text)

    def get_button_text(self, button):
        try:
            return button.find_element(By.CSS_SELECTOR, ".button-label").text
        except NoSuchElementException:
            return button.find_element(By.CSS_SELECTOR, ".label").text

    def handle_farming(self, button):
        logging.info(f"Account {self.serial_number}: Farming is active. The account is currently farming. Skipping this account.")
        try:
            time_left = self.driver.find_element(By.CSS_SELECTOR, "div.time-left").text
            logging.info(f"Account {self.serial_number}: Remaining time to next claim opportunity: {time_left}")
        except NoSuchElementException:
            logging.warning(f"Account {self.serial_number}: Timer not found after detecting farming status.")

    def start_farming(self, button):
        button.click()
        logging.info(f"Account {self.serial_number}: Clicked on 'Start farming'.")
        sleep_time = random.randint(20, 30)
        logging.info(f"Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)
        self.handle_farming(button)
        if not self.is_farming_active():
            raise Exception(f"Account {self.serial_number}: Farming did not start successfully.")

    def claim_tokens(self, button, amount_text):
        sleep_time = random.randint(5, 15)
        logging.info(f"Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)
        logging.info(f"Account {self.serial_number}: Account has {amount_text} claimable tokens. Trying to claim.")

        # CHECK FOR IMG BUTTON 1
        try:
            img1_button = WebDriverWait(self.driver, 1).until(
                EC.element_to_be_clickable((By.XPATH, "/html[1]/body[1]/div[1]/div[1]/div[1]/div[2]/img[2]"))
            )
            img1_button.click()
            logging.info(f"Account {self.serial_number}: New event image №1 clicked")
            time.sleep(2)
        except TimeoutException:
            logging.warning(f"Account {self.serial_number}: img1_button not found. Skipping...")

        # CHECK FOR IMG BUTTON 2
        try:
            img2_button = WebDriverWait(self.driver, 1).until(
                EC.element_to_be_clickable((By.XPATH, "/html[1]/body[1]/div[1]/div[1]/div[1]/div[2]/img[1]"))
            )
            img2_button.click()
            logging.info(f"Account {self.serial_number}: New event image №2 clicked")
            time.sleep(2)
        except TimeoutException:
            logging.warning(f"Account {self.serial_number}: img2_button not found. Skipping...")
        
        button.click() 
        logging.info(f"Account {self.serial_number}: Click successful. 10s sleep, waiting for button to update to 'Start Farming'...")
        time.sleep(10)
  
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".label"))
        )

        start_farming_button = self.wait_for_element(By.CSS_SELECTOR, ".label")
        start_farming_button.click() 
        logging.info(f"Account {self.serial_number}: Second click successful on 'Start farming'")
        sleep_time = random.randint(5, 15)
        logging.info(f"Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)
        self.handle_farming(start_farming_button)
        if not self.is_farming_active():
            raise Exception(f"Account {self.serial_number}: Farming did not start successfully.")

    def check_balance(self):
        logging.info(f"Account {self.serial_number}: Trying to get total balance")
        try:
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                self.driver.switch_to.frame(iframes[0])

            balance_elements = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "div.profile-with-balance .kit-counter-animation.value .el-char-wrapper .el-char"))
            )
            balance = ''.join([element.text for element in balance_elements])
            logging.info(f"Account {self.serial_number}: Current balance: {balance}")
            sleep_time = random.randint(5, 15)
            logging.info(f"Sleeping for {sleep_time} seconds.")
            time.sleep(sleep_time)
            return float(balance.replace(',', ''))

        except TimeoutException:
            logging.warning(f"Account {self.serial_number}: Failed to find the balance element.")
            return None

    def wait_for_element(self, by, value, timeout=10):
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )

    def wait_for_elements(self, by, value, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_all_elements_located((by, value))
        )

    def is_farming_active(self):
        try:
            self.driver.find_element(By.CSS_SELECTOR, "div.time-left")
            return True
        except NoSuchElementException:
            return False

def read_accounts_from_file():
    with open('accounts.txt', 'r') as file:
        return [line.strip() for line in file.readlines()]

def write_accounts_to_file(accounts):
    with open('accounts.txt', 'w') as file:
        for account in accounts:
            file.write(f"{account}\n")

def process_accounts():
    while True: 
        accounts = read_accounts_from_file()
        random.shuffle(accounts)
        write_accounts_to_file(accounts)

        for account in accounts:
            retry_count = 0
            success = False
            while retry_count < 3 and not success:
                bot = TelegramBotAutomation(account)
                try:
                    bot.navigate_to_bot()
                    bot.send_message("https://t.me/retg54erg45g4e")
                    bot.click_link()
                    bot.check_claim_button()
                    logging.info(f"Account {account}: Processing completed successfully.")
                    success = True  
                except Exception as e:
                    logging.warning(f"Account {account}: Error occurred on attempt {retry_count + 1}: {e}")
                    retry_count += 1  
                finally:
                    logging.info("-------------END-----------")
                    bot.browser_manager.close_browser()
                    logging.info("-------------END-----------")
                    sleep_time = random.randint(5, 15)
                    logging.info(f"Sleeping for {sleep_time} seconds.")
                    time.sleep(sleep_time)
                
                if retry_count >= 3:
                    logging.warning(f"Account {account}: Failed after 3 attempts.")

            if not success:
                logging.warning(f"Account {account}: Moving to next account after 3 failed attempts.")
                continue 

        logging.info("All accounts processed. Waiting 8 hours before restarting.")
        for hour in range(8):
            logging.info(f"Waiting... {8 - hour} hours left till restart.")
            time.sleep(60 * 60)  

        logging.info("Shuffling accounts for the next cycle.")

if __name__ == "__main__":
    process_accounts()
