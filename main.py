import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime

def print_with_time(message):
    print(f"{datetime.now()}: {message}")

class TelegramBotAutomation:
    def __init__(self, serial_number):
        self.serial_number = serial_number
        self.driver = None
        print_with_time(f"Initializing automation for account {serial_number}")
        self.start_browser()

    def check_balance(self):
        print_with_time(f"Account {self.serial_number}: Trying to get total balance")
        try:
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                self.driver.switch_to.frame(iframes[0])

            balance_elements = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "div.profile-with-balance .kit-counter-animation.value .el-char-wrapper .el-char"))
            )
            balance = ''.join([element.text for element in balance_elements])
            print_with_time(f"Account {self.serial_number}: Current balance: {balance}")

        except TimeoutException:
            print_with_time(f"Account {self.serial_number}: Failed to find the balance element.")

    def start_browser(self):
        response = requests.get('http://local.adspower.net:50325/api/v1/browser/start', params={'serial_number': self.serial_number, 'headless': 1})
        data = response.json()
        if data['code'] == 0:
            selenium_address = data['data']['ws']['selenium']
            webdriver_path = data['data']['webdriver']
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", selenium_address)
            service = Service(executable_path=webdriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print_with_time(f"Account {self.serial_number}: Browser started successfully.")
        else:
            print_with_time(f"Account {self.serial_number}: Failed to start the browser.")
    

    def navigate_to_bot(self):
        self.driver.get("https://web.telegram.org/k/")
        print_with_time(f"Account {self.serial_number}: Navigated to Telegram web.")

    def send_message(self, message):
        chat_input_area = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/input[1]'))
        )
        chat_input_area.click()
        chat_input_area.send_keys(message)

        search_area = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[3]/div[2]/div[2]/div[2]/div[1]/div[1]/div[1]/div[2]/ul[1]/a[1]/div[1]'))
        )
        search_area.click()
        print_with_time(f"Account {self.serial_number}: Group searched.")

    def click_link(self):
        link = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='t.me/BlumCryptoBot/app?startapp']"))
        )
        link.click()

        launch_click = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html[1]/body[1]/div[7]/div[1]/div[2]/button[1]/div[1]"))
        )
        launch_click.click()
        print_with_time(f"Account {self.serial_number}: BLUM STARTED")

    def check_claim_button(self):
        print_with_time(f"Account {self.serial_number}: Sleeping 30 seconds")
        time.sleep(30)  
        print_with_time(f"Account {self.serial_number}: Sleeping done")
        if not self.switch_to_iframe():
            print_with_time(f"Account {self.serial_number}: No iframes found")
            return
        
        self.check_balance()
        self.process_buttons()

    def switch_to_iframe(self):
        self.driver.switch_to.default_content()
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            self.driver.switch_to.frame(iframes[0])
            return True
        return False

    def process_buttons(self):
        try:
            buttons = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".farming-buttons-wrapper .kit-button"))
            )
            print_with_time(f"Account {self.serial_number}: Found {len(buttons)} buttons")
            for button in buttons:
                self.process_single_button(button)
        except (TimeoutException, NoSuchElementException) as e:
            print_with_time(f"Account {self.serial_number}: Exception occurred: {e}")

    def process_single_button(self, button):
        try:
            button_text = self.get_button_text(button)
        except NoSuchElementException:
            print_with_time(f"Account {self.serial_number}: Button label not found.")
            return
        
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
        print_with_time(f"Account {self.serial_number}: Farming is active. The account is currently farming. Skipping this account.")
        try:
            time_left = self.driver.find_element(By.CSS_SELECTOR, "div.time-left").text
            print_with_time(f"Account {self.serial_number}: Remaining time to next claim opportunity: {time_left}")
        except NoSuchElementException:
            print_with_time(f"Account {self.serial_number}: Timer not found after detecting farming status.")

    def start_farming(self, button):
        button.click()
        print_with_time(f"Account {self.serial_number}: Clicked on 'Start farming'. Sleep 30 seconds and checking balance after:")
        time.sleep(30)
        self.check_balance()

    def claim_tokens(self, button, amount_text):
        print_with_time(f"Account {self.serial_number}: Account has {amount_text} claimable tokens. Trying to claim.")
        button.click() 
        print_with_time(f"Account {self.serial_number}: Click successful. 10s sleep, waiting for button to update to 'Start Farming'...")
        time.sleep(10)
  
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".label"))
        )

        start_farming_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".label"))
        )
        start_farming_button.click() 
        print_with_time(f"Account {self.serial_number}: Second click successful on 'Start farming'. Check balance after:")
        self.check_balance()


    def close_browser(self):
        try:
            response = requests.get('http://local.adspower.net:50325/api/v1/browser/stop', params={'serial_number': self.serial_number})
            data = response.json()
            if data['code'] == 0:
                print_with_time(f"Account {self.serial_number}: Browser closed successfully.")
            else:
                print_with_time(f"Account {self.serial_number}: Failed to close the browser. Error: {data['msg']}")
        except Exception as e:
            print_with_time(f"Account {self.serial_number}: Exception occurred when trying to close the browser: {str(e)}")


def read_accounts_from_file():
    with open('accounts.txt', 'r') as file:
        return [line.strip() for line in file.readlines()]

if __name__ == "__main__":
    while True: 
        accounts = read_accounts_from_file()
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
                    print_with_time(f"Account {account}: Processing completed successfully.")
                    success = True  
                except Exception as e:
                    print_with_time(f"Account {account}: Error occurred on attempt {retry_count + 1}: {e}")
                    retry_count += 1  
                finally:
                    print_with_time("-------------END-----------")
                    bot.close_browser()
                    time.sleep(5)
                
                if retry_count >= 3:
                    print_with_time(f"Account {account}: Failed after 3 attempts.")

            if not success:
                print_with_time(f"Account {account}: Moving to next account after 3 failed attempts.")
                continue 

        print_with_time("All accounts processed. Waiting 8 hours and 5 minutes before restarting.")
        for minute in range(485): 
            if minute % 60 == 0:  
                hours_left = (485 - minute) // 60
                minutes_left = (485 - minute) % 60
                print_with_time(f"Waiting... {hours_left} hours and {minutes_left} minutes left till restart.")
            time.sleep(60)  
