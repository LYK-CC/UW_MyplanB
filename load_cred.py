import json

def load_courses_config(file_path="courses.json"):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: CANNOT FIND {file_path}")
        raise FileNotFoundError
    except json.JSONDecodeError:
        print(f"ERROR: {file_path} file has syntax issue")
        raise SyntaxError
    
def load_credentials(file_path="config.txt"):
    creds = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    key, value = line.strip().split(":", 1)
                    creds[key] = value
        return creds
    except FileNotFoundError:
        print(f"CANNOT LOCATE {file_path}")
        raise FileNotFoundError