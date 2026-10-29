import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, redirect, url_for
from flask_wtf.csrf import CSRFProtect

# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE, override=True)

# =========================================================
# IMPORT BLUEPRINTS
# =========================================================

from routes.auth import auth
from routes.dashboard import dashboard
from routes.disaster import disaster
from routes.resources import resource
from routes.shelters import shelters
from routes.vehicles import vehicles
from routes.volunteers import volunteers
from routes.requests import requests
from routes.reports import reports
from routes.settings import settings

# =========================================================
# CREATE APPLICATION
# =========================================================

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError(
        "SECRET_KEY is missing. Add it to your .env file "
        "or configure it in your deployment environment."
    )

# =========================================================
# CSRF PROTECTION
# =========================================================

csrf = CSRFProtect(app)

# =========================================================
# REGISTER BLUEPRINTS
# =========================================================

app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(disaster)
app.register_blueprint(resource)
app.register_blueprint(shelters)
app.register_blueprint(vehicles)
app.register_blueprint(volunteers)
app.register_blueprint(requests)
app.register_blueprint(reports)
app.register_blueprint(settings)

# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return redirect(url_for("auth.login"))

# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)
