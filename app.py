from flask import Flask, redirect, url_for
from flask_wtf.csrf import CSRFProtect

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


app = Flask(__name__)


app.secret_key = "drrms-development-secret-key"


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

    return redirect(
        url_for("auth.login")
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(debug=True)