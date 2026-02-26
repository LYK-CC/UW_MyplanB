import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- path ---
CHROME_DRIVER_PATH = r"C:\Users\ryanm\OneDrive - UW\Desktop\chromedriver.exe"
TEMP_USER_DATA = r"C:\Users\ryanm\Desktop\Chrome_DUO"

# --- GVoice Full XPath ---
XPATH_ANSWER = "//button[@aria-label='Answer call']"
XPATH_KEYPAD = "//button[@aria-label='Open keypad']"
XPATH_DIGIT_1 = "//button[contains(@aria-label, '1')]"

def start_voice_monitor():

    chrome_options = Options() 
    chrome_options.add_argument(f"--user-data-dir={TEMP_USER_DATA}")
    #chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    #chrome_options.add_argument("--use-fake-ui-for-media-stream")
    #chrome_options.add_argument('--disable-backgrounding-occluded-windows')
    #chrome_options.add_argument('--disable-renderer-backgrounding')

    try:
        driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=chrome_options)
        wait = WebDriverWait(driver, 3)
        
    except Exception as e:
        print(f"google voice startup error {e}")


    try:
        driver.get("https://voice.google.com/u/0/calls")
        #wait = WebDriverWait(driver, 2)
        print(">>> Monitoring...")

        running = True
        while running:
            try:
                answer_btn = wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_ANSWER)))
                print(answer_btn)
                if answer_btn:
                    print("caught call...")
                    driver.execute_script("arguments[0].click();", answer_btn)
                    
                    time.sleep(1) 
                    keypad_btn = wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_KEYPAD)))
                    driver.execute_script("arguments[0].click();", keypad_btn)
                    
                    time.sleep(0.5)
                    digit_1 = wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_DIGIT_1)))
                    driver.execute_script("arguments[0].click();", digit_1)
                    
                    print("pressed 1")
                    time.sleep(1)
                    running = False
            except Exception:
                time.sleep(1)
            if not running:
                break
    except Exception as e:
        print(f"GVoice Monitor Fail:{e}")
    finally:
        try:
            driver.quit()
            print(">>> [Sys] Google Voice login helper Terminated")
        except:
            pass 
    return True

if __name__ == "__main__":
    start_voice_monitor()

