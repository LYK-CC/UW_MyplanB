UW Course Monitor & Auto-Registrar
A robust automation suite designed to monitor course availability on UW MyPlan and perform high-speed registration via the UW Registration API. This tool includes integrated Duo 2FA automation using Google Voice to ensure a fully hands-free experience.

Core Features
API-Based Registration: Instead of slow UI clicking, the script extracts CSRF tokens and session checksums to send direct POST requests to the UW registration endpoint for near-instant enrollment.

Automatic Duo Authentication: Utilizes a specialized monitor to detect incoming Duo phone calls on Google Voice, automatically answering and pressing "1" to authorize the login.

Session Maintenance: A dedicated background thread periodically refreshes the session and monitors health to prevent timeout during long monitoring periods.

Intelligent Logic:

Handles single lectures or lecture + quiz/lab combinations.

Parses registration responses to identify successes, time conflicts, or "already enrolled" statuses.

Headless Support: Can run in the background (Headless mode) to save system resources.

🛠️ Setup & Configuration
1. Requirements
Python 3.x

Selenium & fake-useragent

ChromeDriver (matching your Chrome version)



2. Credentials (config.txt)
Create a config.txt in the root directory with the following format:

Plaintext
account:YOUR_NETID
password:YOUR_PASSWORD
quarter:20262  # e.g., 2026 Spring
number:1234   # Last 4 digits of your Duo-linked Google Voice number

3. Course List (courses.json)
Define the courses you want to track. The lec and quizzes values correspond to the tbody IDs on the MyPlan page:

JSON
{
    "PSYCH311": {
        "url": "https://myplan.uw.edu/course/#/courses/CSE311",
        "blocks": [
            { "lec": "spring-b", "quizzes": ["spring-aa", "spring-ab","spring-ac"] }
        ]
    }
}

Usage
Set Paths: Open Monitor_space.py and update the CHROME_DRIVER_PATH and DEBUG_PROFILE_DIR to match your local environment.

Run the Monitor:

Bash
python Monitor_space.py
Workflow:

The script initializes a session and handles Duo via the Google Voice helper.

It begins cycling through the URLs provided in courses.json.

Once a section status changes to "Open," it immediately triggers the register_sections API call.

File Structure
Monitor_space.py: The main execution script that manages the monitoring loop and registration logic.

login_manager.py: Handles WebDriver initialization, UW NetID login, and API request construction.

Monitor_DUOAUTH.py: A specialized script that automates the Google Voice interface to bypass Duo 2FA.

load_cred.py: Utility to parse configuration files.

Disclaimer
This tool is for educational purposes only. Automated registration may violate university policy. Use responsibly and at your own risk.