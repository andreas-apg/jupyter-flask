import secrets
import os

ENV_FILE = ".env"
KEY_NAME = "SECRET_KEY"

def generate_secret_key():
    return secrets.token_hex(32)

def update_env_file(secret_key):
    lines = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            lines = f.readlines()

    key_found = False
    with open(ENV_FILE, "w") as f:
        for line in lines:
            if line.startswith(KEY_NAME + "="):
                f.write(f"{KEY_NAME}={secret_key}\n")
                key_found = True
            else:
                f.write(line)
        if not key_found:
            f.write(f"{KEY_NAME}={secret_key}\n")

if __name__ == "__main__":
    key = generate_secret_key()
    update_env_file(key)
    print(f"SECRET_KEY set in {ENV_FILE}: {key}")
