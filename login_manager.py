import json
import time
import threading
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from Monitor_DUOAUTH import start_voice_monitor
from load_cred import load_credentials
from fake_useragent import UserAgent

class UWSessionManager:
    def __init__(self, chrome_driver_path, netid, password, quarter,number):
        self.chrome_driver_path = chrome_driver_path
        self.netid = netid
        self.password = password
        self.quarter = str(quarter)
        self.driver = None
        self._lock = threading.Lock()
        self.DUO_PHONE_NUMBER = str(number)

        self.quarter_map = {"1": "wi", "2": "sp", "3": "su", "4": "au"}
        
        print("🚀 Initializing Session Manager: Performing immediate login...")
        self.driver = self.login()
        
        self.stop_maintenance = False
        self.maintenance_thread = threading.Thread(target=self._background_maintenance, daemon=True)
        self.maintenance_thread.start()

    def _get_target_path(self):
        year_suffix = self.quarter[2:4]
        q_code = self.quarter[-1]
        q_label = self.quarter_map.get(q_code, "sp")
        return f"{q_label}{year_suffix}"

    def _is_logged_in(self):
        """if session is still valid"""
        if not self.driver:
            return False
        try:
            curr_url = self.driver.current_url
            if "Logout" in curr_url or "idp.u.washington.edu" in curr_url:
                return False

            self.driver.execute_script("return document.readyState")
            return True
        except Exception:
            return False

    def login(self):

        options = Options()
        
        ua = UserAgent()
        user_agent = ua.random
        options.add_argument(f'user-agent={user_agent}')
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'}) 
        options.add_argument('--disable-blink-features=AutomationControlled')

        service = Service(self.chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 15)

        # Google voice login monitor
        threading.Thread(target=start_voice_monitor, daemon=True).start()

        try:
            driver.get("https://register.uw.edu")
            wait.until(EC.presence_of_element_located((By.ID, "weblogin_netid"))).send_keys(self.netid)
            driver.find_element(By.ID, "weblogin_password").send_keys(self.password)
            driver.find_element(By.NAME, "_eventId_proceed").click()


            other_opt = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Other options')]")))
            other_opt.click()
            
            target_phone_xpath = f"//a[.//span[contains(text(), '{self.DUO_PHONE_NUMBER}')] and .//div[contains(text(), 'Phone call')]]"
            target_element = wait.until(EC.element_to_be_clickable((By.XPATH, target_phone_xpath)))
            driver.execute_script("arguments[0].click();", target_element)
            

            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Yes, this is my device')]"))).click()
            
            target_path = self._get_target_path()
            wait.until(lambda d: "duosecurity.com" not in d.current_url)
            
            driver.get(f"https://register.uw.edu/register/#/{target_path}")
            #time.sleep(5) 
            return driver
        except Exception as e:
            print(f"ERROR:! Login failed: {e}")
            driver.quit()
            return None

    def maintain_session(self):
        with self._lock:
            if not self._is_logged_in():
                print("🔄 Session invalid or expired. Re-logging in now...")
                if self.driver:
                    try: self.driver.quit()
                    except: pass
                self.driver = self.login()
            else:
                # refresh sewssion
                print("Session Healthy, checked:"+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                self.driver.refresh()
                

    def _background_maintenance(self):
        while not self.stop_maintenance:
            time.sleep(random.randint(5*30, 15*45))
            try:
                self.maintain_session()
            except Exception as e:
                print(f"Background maintenance error: {e}")

    def register_sections(self, sln_list):
        if not self.driver or not self._is_logged_in():
            self.maintain_session()

        driver = self.driver
        print(f"📡 Fast-fetching for SLNs: {sln_list}")
        
        # --- dynamically catch cookie ---
        logs = driver.get_log('performance')
        current_token, current_checksum = None, None
        
        for entry in reversed(logs):
            message = json.loads(entry['message'])['message']
            if message.get('method') == 'Network.responseReceived':
                url = message['params']['response'].get('url', '')
                if "api/session" in url:
                    request_id = message['params']['requestId']
                    try:
                        body_node = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                        data = json.loads(body_node['body'])
                        current_token = data.get('csrf')
                        current_checksum = data.get('application', {}).get('checksum')
                        if current_token: break
                    except: continue

        if not current_token:
            driver.refresh()
            time.sleep(2)
            logs = driver.get_log('performance')
            current_token, current_checksum = None, None
            for entry in reversed(logs):
                message = json.loads(entry['message'])['message']
                if message.get('method') == 'Network.responseReceived':
                    url = message['params']['response'].get('url', '')
                    if "api/session" in url:
                        request_id = message['params']['requestId']
                        try:
                            body_node = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                            data = json.loads(body_node['body'])
                            current_token = data.get('csrf')
                            current_checksum = data.get('application', {}).get('checksum')
                            if current_token: break
                        except: continue
            #second trial failure
            if not current_token:
                return {"status": "error", "message": "Failed to extract CSRF from current session."}
        
        # --- 2. JS Fetch ---
        payload_str = json.dumps([{"action": "A", "section": {"sln": str(sln)}, "gradingSystem": "0"} for sln in sln_list])
        fetch_script = f"""
        var uaData = await navigator.userAgentData.getHighEntropyValues(["brands", "platform", "mobile"]);
        var brandsHeader = uaData.brands.map(b => `"${{b.brand}}";v="${{b.version}}"`).join(", ");
        var response = await fetch("https://register-app-api.sps.sis.uw.edu/api/registration/{self.quarter}", {{ 
            "method": "POST",
            "headers": {{
                "content-type": "application/json",
                "x-csrf-token": "{current_token}",
                "x-sis-api-checksum": "{current_checksum}",
                "sec-ch-ua": brandsHeader,
                "sec-ch-ua-platform": `"${{uaData.platform}}"`,
                "sec-ch-ua-mobile": uaData.mobile ? "?1" : "?0"
            }},
            "body": '{payload_str}',
            "credentials": "include"
        }});
        return {{ "status": response.status, "body": await response.text() }};
        """

        try:
            res = driver.execute_async_script(f"const run = async () => {{ {fetch_script} }}; run().then(arguments[0]);")
            if res['status'] != 200:
                self.maintain_session() # relogin triggered
                self.register_sections(self, sln_list)
            return res
        except Exception as e:
            return {"status": "exception", "message": str(e)}


if __name__ == "main":
    CHROME_DRIVER_PATH = r"FILL IN PATH" #TODO
    config = load_credentials()
    NETID = config.get("account")
    PASSWORD = config.get("password")
    QUARTER = config.get("quarter")
    NUMBER = config.get("number")


    uw_api = UWSessionManager(
        chrome_driver_path=CHROME_DRIVER_PATH,
        netid=NETID,
        password=PASSWORD,
        quarter=QUARTER,
        number=NUMBER
    )

    response = uw_api.register_sections(["12473", "12474"])
    print(f"Final Status: {response['status']}")