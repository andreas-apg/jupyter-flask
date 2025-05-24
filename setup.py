import subprocess
import sys
import os

RUN_SCRIPT = "run.py"
print("Checking and installing required packages...")
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
except subprocess.CalledProcessError:
    print("Failed to install required packages.")
    sys.exit(1)

print("Generating .env file...")
subprocess.run([sys.executable, "generate_env.py"])

print("Generating SECRET_KEY...")
subprocess.run([sys.executable, "generate_secret.py"])

print("Launching development server...")
subprocess.run([sys.executable, "run.py"])

print("Setup complete.")