import os
import re
import time
import hmac
import hashlib
import secrets
import requests

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session, current_app
)
from werkzeug.security import generate_password_hash, check_password_hash
from utils.database import get_db_connection


auth = Blueprint("auth", __name__)

EMAIL_PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
PHONE_PATTERN = r"^\d{7,15}$"


# =========================================================
# OTP HELPERS
# =========================================================

def make_otp_hash(email, otp):
    secret = current_app.secret_key

    if not secret:
        raise RuntimeError("Flask SECRET_KEY is not configured.")

    return hmac.new(
        str(secret).encode("utf-8"),
        f"{email}:{otp}".encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def clear_reset_session():
    for key in (
        "reset_email",
        "reset_otp_hash",
        "reset_otp_expires",
        "reset_otp_attempts",
        "reset_verified",
        "reset_verified_until"
    ):
        session.pop(key, None)


# =========================================================
# REGISTER
# =========================================================

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not full_name or not 2 <= len(full_name) <= 100:
            flash("Full name must be between 2 and 100 characters.", "error")
            return redirect(url_for("auth.register"))

        if (
            not email
            or len(email) > 100
            or not re.fullmatch(EMAIL_PATTERN, email)
        ):
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("auth.register"))

        if not re.fullmatch(PHONE_PATTERN, phone):
            flash("Phone number must contain 7 to 15 digits.", "error")
            return redirect(url_for("auth.register"))

        if not password or len(password) < 8 or len(password) > 255:
            flash("Password must be between 8 and 255 characters.", "error")
            return redirect(url_for("auth.register"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("auth.register"))

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                "SELECT user_id FROM users WHERE email = %s",
                (email,)
            )

            if cursor.fetchone():
                flash("Email address is already registered.", "error")
                return redirect(url_for("auth.register"))

            hashed_password = generate_password_hash(password)

            cursor.execute(
                """
                INSERT INTO users
                    (full_name, email, password, role, phone, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    full_name,
                    email,
                    hashed_password,
                    "volunteer",
                    phone,
                    "active"
                )
            )

            user_id = cursor.lastrowid

            cursor.execute(
                "INSERT INTO volunteers (user_id) VALUES (%s)",
                (user_id,)
            )

            connection.commit()

            flash("Registration successful! You can now login.", "success")
            return redirect(url_for("auth.login"))

        except Exception:
            if connection:
                connection.rollback()

            current_app.logger.exception("Registration error")
            flash("Something went wrong during registration.", "error")
            return redirect(url_for("auth.register"))

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "error")
            return redirect(url_for("auth.login"))

        if len(email) > 100 or not re.fullmatch(EMAIL_PATTERN, email):
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("auth.login"))

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT user_id, full_name, email, password, role, status
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            user = cursor.fetchone()

            if not user or not check_password_hash(
                user["password"], password
            ):
                flash("Invalid email or password.", "error")
                return redirect(url_for("auth.login"))

            if user["status"] != "active":
                flash("Your account is not active.", "error")
                return redirect(url_for("auth.login"))

            session.clear()
            session["user_id"] = user["user_id"]
            session["full_name"] = user["full_name"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            return redirect(url_for("dashboard.dashboard_home"))

        except Exception:
            current_app.logger.exception("Login error")
            flash("Something went wrong during login.", "error")
            return redirect(url_for("auth.login"))

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    return render_template("login.html")


# =========================================================
# FORGOT PASSWORD - SEND OTP THROUGH BREVO
# =========================================================

@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if not email or len(email) > 100 or not re.fullmatch(
            EMAIL_PATTERN, email
        ):
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("auth.forgot_password"))

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                "SELECT user_id, email FROM users WHERE email = %s",
                (email,)
            )
            user = cursor.fetchone()

        except Exception:
            current_app.logger.exception("Forgot password database error")
            flash("Unable to process your request. Please try again.", "error")
            return redirect(url_for("auth.forgot_password"))

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        # Always start a fresh reset attempt.
        clear_reset_session()

        # The fallback OTP hash prevents account discovery through
        # different responses when an email is unknown or sending fails.
        otp = f"{secrets.randbelow(900000) + 100000}"
        otp_hash = make_otp_hash(email, otp)
        email_sent = False

        if user:
            api_key = os.getenv("BREVO_API_KEY")
            sender_email = os.getenv("BREVO_SENDER_EMAIL")
            sender_name = os.getenv("BREVO_SENDER_NAME", "DRRMS")

            if api_key and sender_email:
                try:
                    response = requests.post(
                        "https://api.brevo.com/v3/smtp/email",
                        headers={
                            "api-key": api_key,
                            "Content-Type": "application/json",
                            "accept": "application/json"
                        },
                        json={
                            "sender": {
                                "name": sender_name,
                                "email": sender_email
                            },
                            "to": [{"email": email}],
                            "subject": "DRRMS Password Reset OTP",
                            "textContent": (
                                f"Your DRRMS password reset OTP is {otp}.\n\n"
                                "This code expires in 5 minutes. "
                                "If you did not request this, ignore this email."
                            )
                        },
                        timeout=15
                    )

                    email_sent = response.status_code in (200, 201, 202)

                    if not email_sent:
                        current_app.logger.error(
                            "Brevo rejected the email. HTTP status: %s",
                            response.status_code
                        )

                except requests.RequestException:
                    current_app.logger.exception("Brevo email request failed")

        if not email_sent:
            # No usable OTP is sent for unknown accounts or delivery failures.
            otp_hash = make_otp_hash(
                email,
                f"{secrets.randbelow(900000) + 100000}"
            )

        session["reset_email"] = email
        session["reset_otp_hash"] = otp_hash
        session["reset_otp_expires"] = time.time() + 300
        session["reset_otp_attempts"] = 0

        flash(
            "If the email is registered, a reset OTP has been sent.",
            "success"
        )
        return redirect(url_for("auth.verify_reset_otp"))

    return render_template("forgot_password.html")


# =========================================================
# VERIFY RESET OTP
# =========================================================

@auth.route("/verify-reset-otp", methods=["GET", "POST"])
def verify_reset_otp():

    if not session.get("reset_email") or not session.get("reset_otp_hash"):
        flash("Please request a password reset OTP first.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        otp = request.form.get("otp", "").strip()

        if time.time() > session.get("reset_otp_expires", 0):
            clear_reset_session()
            flash("OTP has expired. Please request a new one.", "error")
            return redirect(url_for("auth.forgot_password"))

        attempts = session.get("reset_otp_attempts", 0)

        if attempts >= 5:
            clear_reset_session()
            flash("Too many attempts. Please request a new OTP.", "error")
            return redirect(url_for("auth.forgot_password"))

        session["reset_otp_attempts"] = attempts + 1

        valid_format = re.fullmatch(r"\d{6}", otp) is not None
        submitted_hash = make_otp_hash(
            session["reset_email"],
            otp if valid_format else "invalid-code"
        )

        if not valid_format or not hmac.compare_digest(
            submitted_hash,
            session["reset_otp_hash"]
        ):
            flash("Invalid OTP. Please try again.", "error")
            return redirect(url_for("auth.verify_reset_otp"))

        session.pop("reset_otp_hash", None)
        session.pop("reset_otp_expires", None)
        session.pop("reset_otp_attempts", None)

        session["reset_verified"] = True
        session["reset_verified_until"] = time.time() + 300

        return redirect(url_for("auth.reset_password"))

    return render_template("verify_reset_otp.html")


# =========================================================
# RESET PASSWORD
# =========================================================

@auth.route("/reset-password", methods=["GET", "POST"])
def reset_password():

    if (
        not session.get("reset_verified")
        or not session.get("reset_email")
        or time.time() > session.get("reset_verified_until", 0)
    ):
        clear_reset_session()
        flash("Please verify a new OTP before resetting your password.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(password) < 8 or len(password) > 255:
            flash("Password must be between 8 and 255 characters.", "error")
            return redirect(url_for("auth.reset_password"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("auth.reset_password"))

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                "SELECT user_id FROM users WHERE email = %s",
                (session["reset_email"],)
            )

            if not cursor.fetchone():
                connection.rollback()
                clear_reset_session()
                flash("Unable to reset the password. Please try again.", "error")
                return redirect(url_for("auth.forgot_password"))

            cursor.execute(
                "UPDATE users SET password = %s WHERE email = %s",
                (
                    generate_password_hash(password),
                    session["reset_email"]
                )
            )

            connection.commit()
            clear_reset_session()

            flash("Password reset successful. Please log in.", "success")
            return redirect(url_for("auth.login"))

        except Exception:
            if connection:
                connection.rollback()

            current_app.logger.exception("Password reset error")
            flash("Unable to reset your password. Please try again.", "error")
            return redirect(url_for("auth.reset_password"))

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    return render_template("reset_password.html")


# =========================================================
# LOGOUT
# =========================================================

@auth.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("auth.login"))