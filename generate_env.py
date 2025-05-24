import os
import platform

DEV_MODE = "False"

ADMIN_USERS = "admin,bdmin"
REQUIREMENTS_FILE = "requirements.txt"
TMP_DIR = "/tmp/jupyter_admin" if platform.system() != "Windows" else "/tmp/jupyter_admin"
PROGRAM_DIR = "/var/lib/jupyter-admin" if platform.system() != "Windows" else "/ProgramData/jupyter_admin"
system_dir = ".local/share/jupyterlab/users" if platform.system() != "Windows" else "/Documents/jupyterlab/users"
DATA_DIR = "data" if DEV_MODE == "True" else system_dir

USERS_FILE = os.path.join(PROGRAM_DIR, "users.json")
LOG_FILE = os.path.join(PROGRAM_DIR, "usage_log.json")
LOCK_FILE = os.path.join(TMP_DIR, "gpu.lock")
JUPYTER_PID_FILE = os.path.join(TMP_DIR, "jupyter.pid")
SECRET_KEY = ""

def set_env_var(key, value):
    return f"{key}={value}"

def write_env_file():
    lines = [
        set_env_var("DEV_MODE", DEV_MODE),
        set_env_var("ADMIN_USERS", ADMIN_USERS),
        set_env_var("REQUIREMENTS_FILE", REQUIREMENTS_FILE),
        set_env_var("DATA_DIR", DATA_DIR),
        set_env_var("TMP_DIR", TMP_DIR),
        set_env_var("PROGRAM_DIR", PROGRAM_DIR),
        set_env_var("USERS_FILE", USERS_FILE),
        set_env_var("LOG_FILE", LOG_FILE),
        set_env_var("LOCK_FILE", LOCK_FILE),
        set_env_var("JUPYTER_PID_FILE", JUPYTER_PID_FILE),
        set_env_var("SECRET_KEY", SECRET_KEY)
    ]

    with open(".env", "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Generated .env with default values.")

if __name__ == "__main__":
    write_env_file()