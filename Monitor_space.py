from sys import exception
import time
import re
import subprocess
import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import logging
import sys
import logging
import threading

from fake_useragent import UserAgent
from load_cred import load_credentials, load_courses_config
from login_manager import UWSessionManager



config = load_credentials()
account = config.get("account")
password = config.get("password")
quarter = config.get("quarter")
number = config.get("number")

def reload_course_monitor_list():
    global COURSES_TO_MONITOR
    COURSES_TO_MONITOR = load_courses_config()
reload_course_monitor_list()

CHROME_DRIVER_PATH = r"C:\Users\ryanm\OneDrive - UW\Desktop\chromedriver.exe"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DEBUG_PROFILE_DIR = r"C:\Users\ryanm\Desktop\Chrome_MAIN"

HEADLESS_MODE = True

uw_api = UWSessionManager(
        chrome_driver_path=CHROME_DRIVER_PATH,
        netid=account,
        password=password,
        quarter=quarter,
        number=number
)
print("UW API Initialized")


# get log
logger = logging.getLogger()

# log file config
logger.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')

# empty log file
file_handler = logging.FileHandler("monitor_log.log", mode='w', encoding='utf-8')
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)




def get_section_data(driver, tbody_id):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            sln_raw = driver.find_element(By.XPATH, f"//*[@id='{tbody_id}']/tr[1]/td[6]").text
            sln = "".join(re.findall(r'\d+', sln_raw)) 
            
            status_raw = driver.find_element(By.XPATH, f"//*[@id='{tbody_id}']/tr[1]/td[7]").text
            is_open = "Open" in status_raw 
            
            return {"sln": sln, "open": is_open, "text": status_raw.splitlines()[0]}
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)  
                continue
            else:
                raise Exception(f"tried {max_retries} times but still failed to get{tbody_id}: {e}")
    
def process_uw_response(raw_response):
    try:
        # Handle both string and dict inputs
        data = json.loads(raw_response) if isinstance(raw_response, str) else raw_response
        body = json.loads(data.get('body', '{}'))
        
        # 1. Check for immediate success
        if body.get("transMsg") == "RECORD UPDATED" or body.get("nextAction") == "success":
            return "SUCCESS", "Registered"

        # 2. Analyze the Registration Changes for conflicts
        for change in body.get("registrationChanges", []):
            # This is the SLN you sent in your request
            attempted_sln = str(change.get("section", {}).get("sln", ""))
            
            for msg in change.get("messages", []):
                text = msg.get("messageText", "")
                
                if "meets at the same time as SLN" in text:
                    match = re.search(r'SLN (\d+)', text)
                    conflict_sln = match.group(1) if match else ""
                    
                    # LOGIC: If it conflicts with itself, it's already in the schedule.
                    if conflict_sln == attempted_sln:
                        # Matches Payload 1
                        return "ALREADY_IN", f"SLN {attempted_sln} is already in your schedule (Self-Conflict)."
                    
                    # LOGIC: If it conflicts with a different SLN, it's a schedule overlap.
                    else:
                        # Matches Payload 2
                        return "CONFLICT", f"Time conflict with existing SLN: {conflict_sln}"

        # 3. Handle other errors (Prerequisites, Section Full, etc.)
        return "ERROR", body.get("transMsg", "Unknown Registration Error")

    except Exception as e:
        return "PARSE_FAIL", f"Logic failure: {str(e)}"

def run_monitor(COURSES_TO_MONITOR, CHROME_DRIVER_PATH, is_headless):
    chrome_options = Options()
    
    if is_headless:
        print(">>> Starting: HEADLESS")
        chrome_options.add_argument("--headless=new") 
        chrome_options.add_argument("--disable-gpu")
    else:
        print(">>> STARTING: NORMAL")
        chrome_options.add_argument("--start-maximized")
        
    chrome_options.add_argument(f"--user-data-dir={DEBUG_PROFILE_DIR}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    ua = UserAgent()
    user_agent = ua.random
    chrome_options.add_argument(f'user-agent={user_agent}')
    
    service = Service(executable_path=CHROME_DRIVER_PATH)
    
    try:

        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get("https://myplan.uw.edu/course/")
        time.sleep(3) 
        try:
            login_btn = driver.find_elements(By.XPATH, '//*[@id="login-google"]')
            if login_btn:
                print(">>> detected login page, logging in...")
                login_btn[0].click()
        except Exception as e:
            print(f"LOGIN to myplan failed: {e}")
            raise Exception("LOGIN FAILED. Cancle headless mode and login manually.")
        time.sleep(5)
        while COURSES_TO_MONITOR:
            for course_key in list(COURSES_TO_MONITOR.keys()):
                info = COURSES_TO_MONITOR[course_key]
                driver.get(info["url"])
                time.sleep(1.2)  # Wait for MyPlan to render
                
                course_registered = False
                
                for block in info["blocks"]:
                    try:
                        lec_data = get_section_data(driver, block["lec"])
                    except Exception as e:
                        logging.error(f"Failed to fetch data for {course_key}: {e}")
                        continue

                    logging.info(f"Checking {course_key}: {lec_data['text']} ({lec_data['sln']})")

                    # CASE 1: Lecture only (No quizzes in this block)
                    if not block["quizzes"]:
                        if lec_data["open"]:
                            print(f"🔥 Slot found for {course_key}! Registering SLN: {lec_data['sln']}")
                            payload = uw_api.register_sections([lec_data['sln']])
                            status, detail = process_uw_response(payload)
                            print(status,detail)
                            #input()
                            if status in ["SUCCESS", "ALREADY_IN"]:
                                print(f"✅ {course_key} Secured: {detail}")
                                course_registered = True
                            elif status == "CONFLICT":
                                print(f"⚠️ Conflict for {course_key}:{detail}")
                                course_registered = True
                            else:
                                print(f"❌ Registration failed for {lec_data['sln']}: {detail}")

                    # CASE 2: Lecture + Quiz combination
                    elif lec_data["open"]:
                        for q_id in block["quizzes"]:
                            try:
                                quiz_data = get_section_data(driver, q_id)
                            except: continue

                            if quiz_data["open"]:
                                slns_to_add = [lec_data['sln'], quiz_data['sln']]
                                print(f"🔥 Combination found! Registering {course_key} SLNs: {slns_to_add}")
                                
                                payload = uw_api.register_sections(slns_to_add)
                                status, detail = process_uw_response(payload)
                                #print(status,detail)
                                #input()
                                if status in ["SUCCESS", "ALREADY_IN"] or detail in ["DUPLICATE ENROLL NOT ALLOWED"]:
                                    print(f"✅ {course_key} Secured: {detail}")
                                    course_registered = True
                                elif status == "CONFLICT":
                                    print(f"⚠️ Conflict for {course_key}:{detail}")
                                    course_registered = True
                                else:
                                    print(f"❌ Registration failed for {lec_data['sln']}: {detail}")

                    
                    if course_registered:
                        del COURSES_TO_MONITOR[course_key]
                        break # break block loop

            if not COURSES_TO_MONITOR:
                print("\n🎯 All courses registered successfully!")
                break

            logging.info(f"Round finished. Sleeping for 3 seconds...")
            time.sleep(3)
            
    except Exception as e:
        print(f"Terminated traceback RunMonitor {e}")
        raise e 
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def threadwrapper():
    while True:
        try:
            if not os.path.exists(DEBUG_PROFILE_DIR): 
                os.makedirs(DEBUG_PROFILE_DIR)
            
            run_monitor(COURSES_TO_MONITOR, CHROME_DRIVER_PATH, HEADLESS_MODE)
            
            break

        except Exception as e:
            print(f"\n[!] ERROR: {e}")
            print(">>> 5 seconds before next trial of connection...")
            time.sleep(5)
if __name__ == "__main__":
    monitor_thread = threading.Thread(target=threadwrapper, daemon=True)
    monitor_thread.start()
 
'''
# %%
response = uw_api.register_sections([18975])
status, detail = process_uw_response(response)
print(status,detail)

'''