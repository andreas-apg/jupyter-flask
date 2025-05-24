import os
from app import create_app
from dotenv import load_dotenv
from waitress import serve
from app.utils import get_local_ipv4

# Load .env to check runtime mode
load_dotenv()

# gets boolean True or False from the .env
dev_mode = os.environ.get("DEV_MODE", "True") == "True"
ip = get_local_ipv4()
port = 5000

app = create_app()

if __name__ == "__main__":
    if dev_mode:
        print(f"Running in DEV mode at http://{ip}:{port} with Flask server...")
        app.run(host="0.0.0.0", port=port)
    else:
        print(f"Running in PROD mode at http://{ip}:{port} with Waitress...")
        serve(app, host="0.0.0.0", port=port)