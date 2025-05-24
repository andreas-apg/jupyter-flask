import os
from flask import Flask
from dotenv import load_dotenv

def create_app():
    load_dotenv()
    
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "fallback-secret")
    
    from .routes import init_routes
    init_routes(app)
    return app

if __name__ == "__main__":
    from . import create_app

    app = create_app()
    dev_mode = os.environ.get("DEV_MODE", "True") == "True"

    if dev_mode:
        print("Running in DEV mode with Flask server...")
        app.run(host="0.0.0.0", port=5000)
    else:
        print("Running in PROD mode with Waitress...")
        from waitress import serve
        serve(app, host="0.0.0.0", port=5000)