from flask import Flask
from .dashboard import dashboard_bp
from .api import api_bp
from dotenv import load_dotenv
import os
load_dotenv()

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(api_bp, url_prefix="/api")

    from .cli import user, device
    app.cli.add_command(user)
    app.cli.add_command(device)
    
    app.config["SECRET_KEY"] = os.getenv("SESSION_SECRET_KEY", "DEFAULTKEY-FAILSAFE-988572397426")
    return app