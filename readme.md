

### **UW Course Registration Automator**
A Python-based automation suite designed to monitor and register for University of Washington courses in real-time. It handles Duo 2FA automatically via Google Voice and uses a hybrid approach of Selenium and direct API injection for high-speed registration.

🛠️ Prerequisites & Installation
1. System Requirements
Python 3.x: Ensure Python is installed and added to your PATH.

Chrome Browser: Installed at the default location.


ChromeDriver: Must match your Chrome version and be placed in the path specified in your scripts. 

2. Required Python Packages
Run the following command to install necessary dependencies:

```Bash
pip install selenium fake-useragent
```
selenium: For browser automation and session handling. 


fake-useragent: To rotate User-Agent headers and avoid bot detection. 


json, threading, time, re: These are part of the Python standard library used throughout the project. 

### **Project Structure**

**login_manager.py**: Manages Selenium drivers, UW login, and executes registration API calls via JS injection. 

**Monitor_DUOAUTH.py**: A specialized script that controls a browser instance to answer Google Voice calls and press '1' for Duo approval.

**Monitor_space.py**: The main entry point that monitors MyPlan course availability and triggers the registration logic.

**load_cred.py**: Utility to parse credentials from config.txt and course configurations from courses.json.

**config.txt**: Stores your NetID, password, target quarter, and Duo phone number.

**courses.json**: Defines which courses and specific section blocks (SLNs) to monitor.

⚙️ Configuration
1. Credentials (config.txt)
Update this file with your UW and Duo details:


```

account:your_netid
password:your_password
quarter:20262
number:1234
```
2. Courses (courses.json)
List the courses you want to watch. The lec and quizzes keys refer to the HTML tbody IDs on the MyPlan page:
```
{
    "PSYCH210": {
        "url": "https://myplan.uw.edu/course/#/courses/PSYCH210",
        "blocks": [
            { "lec": "spring-b", "quizzes": [] }
        ]
    }
}
```
3. Path Setup
In Monitor_space.py and Monitor_DUOAUTH.py, update these variables to match your local system:

**CHROME_DRIVER_PATH**: Full path to your chromedriver.exe.

**DEBUG_PROFILE_DIR / TEMP_USER_DATA**: Local folders for Chrome to store session data, **AND THEY HAVE TO BE DIFFERENT, ONE FOR DUO MONITOR AND ONE FOR SCANNING COURSES!!!!!!!**

**HEADLESS_MODE** = True/False - GUI or NO_GUI for course scanning

### **Usage**
To start the monitoring and registration process, run:

Bash
```
python Monitor_space.py
```
How it works:

**Initial Login**: ****login_manager.py**** starts a browser to log into the UW registration portal. 


**2FA**: ****Monitor_DUOAUTH.py**** runs a background thread to automatically answer the Duo phone call via Google Voice. 

**Monitoring**: ****Monitor_space.py**** scrapes MyPlan every few seconds to check for "Open" status.


**Fast Registration**: When a spot opens, the script extracts session tokens to perform a direct API request for maximum speed. 

### **Disclaimer**
This tool is for educational purposes. Automated registration may be against University of Washington policy. Use at your own risk.
