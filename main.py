import requests
import os
import time
import logging
import json
import random
from beautifultable import BeautifulTable
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
            logging.exception(f"Account {self.serial_number}: Exception in checking browser status")
            return False

    def start_browser(self):
        try:
            if self.check_browser_status():
                logging.info(f"Account {self.serial_number}: Browser already open. Closing the existing browser.")
                self.close_browser()
                time.sleep(5)

            launch_args = json.dumps(["--headless=new"])
            request_url = (
                f'http://local.adspower.net:50325/api/v1/browser/start?'
                f'serial_number={self.serial_number}&ip_tab=1&launch_args={launch_args}'
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
                
                try:
                    self.driver.set_window_size(600, 720)
                except WebDriverException as e:
                    if "Browser window not found" in str(e):
                        logging.error(f"Account {self.serial_number}: Browser window not found, forcing restart")
                        self.close_browser()
                        return False
                    logging.error(f"Account {self.serial_number}: WebDriverException when setting window size:")
                    return False
                
                logging.info(f"Account {self.serial_number}: Browser started successfully.")
                return True
            else:
                logging.warning(f"Account {self.serial_number}: Failed to start the browser. Error: {data['msg']}")
                return False
        except Exception as e:
            logging.exception(f"Account {self.serial_number}: Exception in starting browser")
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
            logging.exception(f"Account {self.serial_number}: General Exception occurred when trying to close the browser")
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
                logging.exception(f"Account {self.serial_number}: Exception occurred when trying to close the browser")

class TelegramBotAutomation:
    def __init__(self, serial_number):
        self.serial_number = serial_number
        self.browser_manager = BrowserManager(serial_number)
        logging.info(f"Initializing automation for account {serial_number}")
        self.browser_manager.start_browser()
        self.driver = self.browser_manager.driver

    def navigate_to_bot(self):
        try:
            time.sleep(2)
            self.driver.get('https://web.telegram.org/k/')
            logging.info(f"Account {self.serial_number}: Navigated to Telegram web.")
            time.sleep(3)
            
            handles = self.driver.window_handles
            target_url = 'https://web.telegram.org/k/'
            
            for handle in handles:
                self.driver.switch_to.window(handle)
                if target_url in self.driver.current_url:
                    logging.info(f"Account {self.serial_number}: Found and switched to correct Telegram tab.")
                    time.sleep(2)
                    return
                    
            logging.error(f"Account {self.serial_number}: Could not find correct Telegram tab.")
            
        except Exception as e:
            logging.error(f"Account {self.serial_number}: Failed at navigate_to_bot():")
            self.browser_manager.close_browser()

    def send_message(self, message):
        try:
            chat_input_area = self.wait_for_element(By.XPATH, '/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/input[1]')
            chat_input_area.click()
            chat_input_area.send_keys(message)

            search_area = self.wait_for_element(By.XPATH, '/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[3]/div[2]/div[2]/div[2]/div[1]/div[1]/div[1]/div[2]/ul[1]/a[1]/div[1]')
            search_area.click()
            logging.info(f"Account {self.serial_number}: Group searched.")
            sleep_time = random.randint(5, 10)
            logging.info(f"Sleeping for {sleep_time} seconds.")
            time.sleep(sleep_time)
        except Exception:
            logging.exception(f"Account {self.serial_number}: Failed at send_message()")

    def click_link(self):
        try:
            link = self.wait_for_element(By.CSS_SELECTOR, "a[href*='t.me/BlumCryptoBot/app?startapp']")
            link.click()
        except NoSuchElementException:
            logging.error(f"Account {self.serial_number}: Failed at click_link() - Link not found")
            return
        except WebDriverException:
            logging.info(f"Account {self.serial_number}: has /k/ telegram version. all good.")
            return
        except Exception:
            logging.exception(f"Account {self.serial_number}: Failed at click_link()")
            return

        try:
            launch_click = self.wait_for_element(By.XPATH, "//body/div[@class='popup popup-peer popup-confirmation active']/div[@class='popup-container z-depth-1']/div[@class='popup-buttons']/button[1]/div[1]")
            launch_click.click()
            logging.info(f"Account {self.serial_number}: Button clicked.")
        except NoSuchElementException:
            logging.info(f"Account {self.serial_number}: No confirmation popup found, continuing.")
        except WebDriverException:
            logging.error(f"Account {self.serial_number}: Failed at click_link() - Launch button click failed")
        except Exception:
            logging.error(f"Account {self.serial_number}: Failed at click_link() - Launch button section")

        logging.info(f"Account {self.serial_number}: BLUM STARTED")
        sleep_time = random.randint(10, 13)
        logging.info(f"Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)

        if not self.switch_to_iframe():
            logging.info(f"Account {self.serial_number}: No iframes found")
            return

        try:
            while True:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, "button.kit-button.is-large.is-primary.is-fill.kit-stories-shared-button")
                    next_button.click()
                    logging.info(f"Account {self.serial_number}: Next button clicked")
                    time.sleep(1)
                except NoSuchElementException:
                    logging.info(f"Account {self.serial_number}: No more Next buttons found, proceeding")
                    break
        except Exception as e:
            logging.error(f"Account {self.serial_number}: Error in Next button loop")

    def check_claim_button(self):
        if not self.switch_to_iframe():
            logging.info(f"Account {self.serial_number}: No iframes found")
            return 0.0, 0, 0
        
        initial_balance, initial_tickets, days = self.check_balance()
        self.handle_daily_reward()
        
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                if self.is_farming_active():
                    logging.info(f"Account {self.serial_number}: Farming is already active")
                    break
                    
                claim_button = self.find_and_scroll_to_element("button.kit-pill-claim.reset.is-state-claim.is-type-default")
                if claim_button:
                    logging.info(f"Account {self.serial_number}: Found claim button, clicking...")
                    try:
                        claim_button.click()
                        time.sleep(5)
                    except Exception as e:
                        logging.error(f"Account {self.serial_number}: Error clicking claim button")
                    continue

                farm_button = self.find_and_scroll_to_element(".kit-pill-claim.reset.is-state-claim.is-type-dark")
                if farm_button:
                    logging.info(f"Account {self.serial_number}: Found farm button, clicking...")
                    try:
                        farm_button.click()
                        time.sleep(5)
                    except Exception as e:
                        logging.error(f"Account {self.serial_number}: Error clicking farm button:")
                    continue

                break

            except Exception as e:
                retry_count += 1
                logging.error(f"Account {self.serial_number}: Error during button check attempt {retry_count}")
                time.sleep(3)
                continue

        if not self.is_farming_active():
            logging.error(f"Account {self.serial_number}: Failed to activate farming after {max_retries} attempts")
        else:
            logging.info(f"Account {self.serial_number}: Successfully activated farming")
            farming_button = self.find_and_scroll_to_element(".kit-pill.reset.is-type-dark.farming")
            if farming_button:
                try:
                    bp_amount = farming_button.find_element(By.CSS_SELECTOR, "div[data-v-bc872879]").text
                    logging.info(f"Account {self.serial_number}: Current farming amount: {bp_amount}")
                except Exception:
                    logging.exception(f"Account {self.serial_number}: Could not get farming amount")

        final_balance, final_tickets, days = self.check_balance()
        return final_balance, final_tickets, days

    def switch_to_iframe(self):
        self.driver.switch_to.default_content()
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            self.driver.switch_to.frame(iframes[0])
            return True
        return False

    def process_buttons(self):
        try:
            claim_button = self.driver.find_element(By.CSS_SELECTOR, "button.kit-pill-claim.reset.is-state-claim.is-type-default")
            if claim_button:
                logging.info(f"Account {self.serial_number}: Found claim button ready to claim")
                claim_button.click()
                time.sleep(10)
                return

            farm_button = self.driver.find_element(By.CSS_SELECTOR, ".kit-pill-claim.reset.is-state-claim.is-type-dark")
            if farm_button:
                logging.info(f"Account {self.serial_number}: Found farm button ready to start")
                farm_button.click()
                time.sleep(10)
                return

            farming_button = self.driver.find_element(By.CSS_SELECTOR, ".kit-pill.reset.is-type-dark.farming")
            if farming_button:
                time.sleep(2)
                bp_amount = farming_button.find_element(By.CSS_SELECTOR, "div[data-v-bc872879]").text
                logging.info(f"Account {self.serial_number}: Currently farming, BP amount: {bp_amount}")
                return

        except NoSuchElementException:
            logging.info(f"Account {self.serial_number}: No actionable buttons found")

    def handle_daily_reward(self):
        try:
            daily_claim = self.find_and_scroll_to_element(".kit-pill-claim.reset.is-state-claim.is-type-default.pill")
            if daily_claim:
                logging.info(f"Account {self.serial_number}: Daily reward ready to claim")
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        time.sleep(2) 
                        daily_claim.click()
                        logging.info(f"Account {self.serial_number}: Successfully claimed daily reward")
                        time.sleep(2)
                        return
                    except Exception as e:
                        if attempt < max_attempts - 1:
                            logging.info(f"Account {self.serial_number}: Retry {attempt + 1} to click daily reward")
                            continue
                        else:
                            logging.error(f"Account {self.serial_number}: Failed to click daily reward after {max_attempts} attempts")
                return

            claimed_button = self.find_and_scroll_to_element(".kit-pill-claim.reset.is-state-claimed.is-type-default.pill")
            if claimed_button:
                next_claim = self.find_and_scroll_to_element("div.subtitle")
                if next_claim:
                    logging.info(f"Account {self.serial_number}: Daily reward already claimed. {next_claim.text}")
                return

        except Exception as e:
            logging.error(f"Account {self.serial_number}: Failed at handle_daily_reward():")

    def check_balance(self):
        logging.info(f"Account {self.serial_number}: Trying to get total balance")
        try:
            balance_containers = self.driver.find_elements(By.CSS_SELECTOR, "div.pages-wallet-asset-points .pages-wallet-asset")
            if len(balance_containers) >= 2:
                bp_container = balance_containers[1]
                balance_element = bp_container.find_element(By.CSS_SELECTOR, ".balance")
                balance_text = balance_element.text
                balance = float(balance_text.replace('BP', '').replace(',', '').strip())
                
                try:
                    streak_element = self.driver.find_element(By.CSS_SELECTOR, "div.widget.has-radius .title")
                    streak_text = streak_element.text
                    days = int(''.join(filter(str.isdigit, streak_text)))
                    logging.info(f"Account {self.serial_number}: Check-in streak: {days} days")
                except Exception as e:
                    logging.warning(f"Account {self.serial_number}: Could not get check-in streak info:")
                    days = 0
                
                tickets = self.get_tickets()
                logging.info(f"Account {self.serial_number}: Current balance: {balance:,.1f} BP")
                logging.info(f"Account {self.serial_number}: Current tickets: {tickets}")
                
                return balance, tickets, days
            else:
                logging.warning(f"Account {self.serial_number}: Not enough balance containers found (found {len(balance_containers)})")
                raise Exception("Balance containers not found")

        except NoSuchElementException:
            logging.error(f"Account {self.serial_number}: Balance elements not found")
            return 0.0, 0, 0
        except ValueError:
            logging.error(f"Account {self.serial_number}: Could not parse balance value")
            return 0.0, 0, 0
        except Exception as e:
            logging.error(f"Account {self.serial_number}: Failed at check_balance():")
            return 0.0, 0, 0

    def get_tickets(self):
        try:
            ticket_element = self.find_and_scroll_to_element("div.default .balance")
            if ticket_element:
                tickets_text = ticket_element.text
                return int(''.join(filter(str.isdigit, tickets_text)))
            return 0
        except Exception:
            logging.warning(f"Account {self.serial_number}: Failed to get tickets")
            return 0

    def wait_for_element(self, by, value, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
        except TimeoutException:
            logging.error(f"Account {self.serial_number}: Timeout waiting for element")
            return None
        except Exception as e:
            logging.error(f"Account {self.serial_number}: Error waiting for element:")
            return None

    def wait_for_elements(self, by, value, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_all_elements_located((by, value))
            )
        except TimeoutException:
            logging.error(f"Account {self.serial_number}: Timeout waiting for elements")
            return []
        except Exception as e:
            logging.error(f"Account {self.serial_number}: Error waiting for elements: ")
            return []

    def is_farming_active(self):
        try:
            self.driver.find_element(By.CSS_SELECTOR, ".kit-pill.reset.is-type-dark.farming")
            return True
        except NoSuchElementException:
            return False

    def get_checkin_streak(self):
        try:
            streak_element = self.driver.find_element(By.CSS_SELECTOR, "div.widget.has-radius .title")
            streak_text = streak_element.text
            days = int(''.join(filter(str.isdigit, streak_text)))
            
            next_claim_element = self.driver.find_element(By.CSS_SELECTOR, "div.widget.has-radius .subtitle")
            next_claim_time = next_claim_element.text
            
            logging.info(f"Account {self.serial_number}: Check-in streak: {days} days")
            logging.info(f"Account {self.serial_number}: Next claim time: {next_claim_time}")
            
            return days, next_claim_time
        except NoSuchElementException:
            logging.warning(f"Account {self.serial_number}: Could not find check-in streak information")
            return 0, ""
        except ValueError as e:
            logging.warning(f"Account {self.serial_number}: Failed to parse check-in streak value")
            return 0, ""

    def scroll_into_view(self, element):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
            time.sleep(1) 
            return True
        except Exception as e:
            logging.error(f"Account {self.serial_number}: Failed to scroll element into view: ")
            return False

    def find_and_scroll_to_element(self, css_selector, max_attempts=3):
        for attempt in range(max_attempts):
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, css_selector)
                if not self.is_element_in_viewport(element):
                    self.scroll_into_view(element)
                return element
            except NoSuchElementException:
                #logging.info(f"Account {self.serial_number}: Element {css_selector} not found on attempt {attempt + 1}")
                self.driver.execute_script("window.scrollBy(0, 300);")
                time.sleep(1)
        return None

    def is_element_in_viewport(self, element):
        try:
            return self.driver.execute_script("""
                var rect = arguments[0].getBoundingClientRect();
                return (
                    rect.top >= 0 &&
                    rect.left >= 0 &&
                    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                );
            """, element)
        except Exception as e:
            logging.error(f"Account {self.serial_number}: Error checking viewport:")
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
        account_data = []
        accounts = read_accounts_from_file()
        random.shuffle(accounts)
        write_accounts_to_file(accounts)

        for account in accounts:
            retry_count = 0
            success = False
            balance = 0.0
            tickets = 0
            days = 0

            while retry_count < 3 and not success:
                bot = None
                try:
                    bot = TelegramBotAutomation(account)
                    if not bot.browser_manager.driver:
                        raise Exception("Browser failed to start")

                    bot.navigate_to_bot()
                    
                    try:
                        bot.send_message("https://t.me/retg54erg45g4e")
                    except Exception as e:
                        logging.error(f"Account {account}: Failed to send message, retrying...")
                        raise 

                    try:
                        bot.click_link()
                        if not bot.switch_to_iframe(): 
                            raise Exception("Failed to find iframe")
                    except Exception as e:
                        logging.error(f"Account {account}: Failed to access BLUM, retrying...")
                        raise 

                    try:
                        balance, tickets, days = bot.check_claim_button()
                        account_data.append((account, balance, tickets, days))
                        logging.info(f"Account {account}: Processing completed successfully.")
                        success = True

                    except Exception as e:
                        retry_count += 1
                        logging.error(f"Account {account}: Failed attempt {retry_count}/3: {str(e)}")
                        if retry_count < 3:
                            logging.info(f"Account {account}: Retrying in 10 seconds...")
                            time.sleep(10)

                except Exception as e:
                    retry_count += 1
                    logging.error(f"Account {account}: Failed attempt {retry_count}/3: {str(e)}")
                    if retry_count < 3:
                        logging.info(f"Account {account}: Retrying in 10 seconds...")
                        time.sleep(10)
                finally:
                    if bot:
                        logging.info("-------------END-----------")
                        bot.browser_manager.close_browser()
                        logging.info("-------------END-----------")
                    sleep_time = random.randint(5, 15)
                    logging.info(f"Sleeping for {sleep_time} seconds.")
                    time.sleep(sleep_time)

            if not success:
                logging.error(f"Account {account}: Failed after 3 attempts, moving to next account.")
                account_data.append((account, 0.0, 0, 0))

        if account_data:
            last_processed_account, last_balance, last_tickets, last_days = account_data[-1]

        table = BeautifulTable()
        table.columns.header = ["Serial Number", "Balance", "Tickets", "Check-in Days"]

        total_balance = 0.0
        total_tickets = 0
        for serial_number, balance, tickets, days in account_data:
            table.rows.append([serial_number, balance, tickets, days])
            total_balance += balance
            total_tickets += tickets

        logging.info("\n" + str(table))
        logging.info(f"Total Balance: {total_balance:,.2f}")
        logging.info(f"Total Tickets: {total_tickets}")

        logging.info("All accounts processed. Waiting 8 hours before restarting.")

        for hour in range(8):
            logging.info(f"Waiting... {8 - hour} hours left till restart.")
            time.sleep(60 * 60)  

        account_data = [(last_processed_account, last_balance, last_tickets, last_days)]
        logging.info("Shuffling accounts for the next cycle.")

if __name__ == "__main__":
    process_accounts()
