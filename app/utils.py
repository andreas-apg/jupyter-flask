import os, json, hashlib, binascii, socket, datetime, logging, psutil
from flask import request
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Pull paths from environment variables
USERS_FILE = os.environ.get("USERS_FILE")
LOG_FILE = os.environ.get("LOG_FILE")
LOCK_FILE = os.environ.get("LOCK_FILE")
JUPYTER_PID_FILE = os.environ.get("JUPYTER_PID_FILE")
ADMIN_USERS = os.environ.get("ADMIN_USERS", "").split(",")

def get_local_ipv4():
    """
    Gets the local ipv4 address for the machine.
    If it fails, returns the localhost 127.0.0.1 address.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def load_users():
    """
    Safely load user data from USERS_FILE.
    Returns empty dict if file doesn't exist, is empty, or contains invalid JSON.
    """
    try:
        if not os.path.exists(USERS_FILE) or os.path.getsize(USERS_FILE) == 0:
            return {}
            
        with open(USERS_FILE, "r") as f:
            data = json.load(f)
            # Validate loaded data is a dictionary
            if not isinstance(data, dict):
                print(f"Warning: {USERS_FILE} didn't contain a JSON object, resetting")
                return {}
            return data
            
    except json.JSONDecodeError as e:
        print(f"Warning: {USERS_FILE} contained invalid JSON: {e}")
        return {}
    except Exception as e:
        print(f"Warning: Unexpected error loading {USERS_FILE}: {e}")
        return {}

def save_users(users):
    """
    Atomically save user data to USERS_FILE.
    Ensures file always contains valid JSON, even if write fails.
    """
    if not isinstance(users, dict):
        raise ValueError("Users data must be a dictionary")
    
    try:
        # Create parent directory if needed
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        
        # Write to temporary file first
        temp_file = f"{USERS_FILE}.tmp"
        with open(temp_file, "w") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
            f.flush()  # Force write to disk
            os.fsync(f.fileno())  # Ensure OS-level write
            
        # Atomic rename (works on Unix and Windows)
        os.replace(temp_file, USERS_FILE)
        
    except Exception as e:
        # Clean up temp file if something went wrong
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise RuntimeError(f"Failed to save users: {e}")

def is_admin(username):
    """Check if the user is an admin"""
    return username in ADMIN_USERS

def hash_password(password, salt):
    """Hash a password with a given salt using SHA-256."""
    return hashlib.sha256((salt + password).encode()).hexdigest()

def jupyter_hash(password):
    """Create a Jupyter-compatible hashed password."""
    salt = binascii.hexlify(os.urandom(8)).decode()
    h = hashlib.sha1()
    h.update((password + salt).encode('utf-8'))
    return f"sha1:{salt}:{h.hexdigest()}"

def get_local_ip():
    """Get the local IP address of the host."""
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)

def log_session_action(username, action):
    """Log session start/end events"""
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "username": username,
        "action": action,
        "ip": request.remote_addr
    }
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        logging.error(f"Failed to write log: {e}")

def get_session_duration():
    """Calculate how long the session has been active"""
    if not os.path.exists(LOCK_FILE): return "0 minutes"
    try:
        lock_time = os.path.getmtime(LOCK_FILE)
        duration = datetime.datetime.now() - datetime.datetime.fromtimestamp(lock_time)
        minutes = int(duration.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}" if minutes >= 1 else "less than a minute"
    except:
        return "unknown duration"

def load_logs():
    """Load all log entries from the log file"""
    if not os.path.exists(LOG_FILE): return []
    logs = []
    with open(LOG_FILE, "r") as f:
        for line in f:
            try: logs.append(json.loads(line))
            except: continue
    return logs

def release_lock():
    """Release the current lock"""
    if os.path.exists(JUPYTER_PID_FILE):
        with open(JUPYTER_PID_FILE, "r") as pf:
            try:
                pid = int(pf.read().strip())
                proc = psutil.Process(pid)
                for child in proc.children(recursive=True):
                    child.kill()
                proc.kill()
                logging.info(f"Force-killed process tree for PID {pid}")
            except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logging.error(f"Error killing process: {e}")

    # Cleanup files
    if os.path.exists(JUPYTER_PID_FILE):
        os.remove(JUPYTER_PID_FILE)
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

