from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from utils.database import get_db_connection
import re


auth = Blueprint("auth", __name__)


# =========================================================
# VALIDATION OPTIONS
# =========================================================

EMAIL_PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
PHONE_PATTERN = r"^\d{7,15}$"


# =========================================================
# REGISTER
# =========================================================

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        # Safely get form values
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")


        # =====================================================
        # FULL NAME VALIDATION
        # =====================================================

        if not full_name:

            flash(
                "Full name is required.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        if len(full_name) < 2 or len(full_name) > 100:

            flash(
                "Full name must be between 2 and 100 characters.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        # =====================================================
        # EMAIL VALIDATION
        # =====================================================

        if not email:

            flash(
                "Email address is required.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        if len(email) > 100 or not re.match(
            EMAIL_PATTERN,
            email
        ):

            flash(
                "Please enter a valid email address.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        # =====================================================
        # PHONE VALIDATION
        # =====================================================

        if not phone:

            flash(
                "Phone number is required.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        if not re.fullmatch(
            PHONE_PATTERN,
            phone
        ):

            flash(
                "Phone number must contain 7 to 15 digits.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        # =====================================================
        # PASSWORD VALIDATION
        # =====================================================

        if not password:

            flash(
                "Password is required.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        if len(password) < 8:

            flash(
                "Password must be at least 8 characters long.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        if len(password) > 255:

            flash(
                "Password cannot exceed 255 characters.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        # =====================================================
        # CONFIRM PASSWORD
        # =====================================================

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        connection = None
        cursor = None


        try:

            connection = get_db_connection()

            cursor = connection.cursor()


            # =================================================
            # CHECK IF EMAIL ALREADY EXISTS
            # =================================================

            cursor.execute(
                """
                SELECT user_id
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            existing_user = cursor.fetchone()


            if existing_user:

                flash(
                    "Email address is already registered.",
                    "error"
                )

                return redirect(
                    url_for("auth.register")
                )


            # =================================================
            # HASH PASSWORD
            # =================================================

            hashed_password = generate_password_hash(
                password
            )


            # =================================================
            # INSERT USER
            # =================================================

            cursor.execute(
                """
                INSERT INTO users
                (
                    full_name,
                    email,
                    password,
                    role,
                    phone,
                    status
                )
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


            # =================================================
            # CREATE VOLUNTEER PROFILE
            # =================================================

            cursor.execute(
                """
                INSERT INTO volunteers
                (user_id)
                VALUES (%s)
                """,
                (user_id,)
            )


            # Commit both operations together
            connection.commit()


            flash(
                "Registration successful! You can now login.",
                "success"
            )

            return redirect(
                url_for("auth.login")
            )


        except Exception as e:

            if connection:

                connection.rollback()


            print(
                "REGISTRATION ERROR:",
                repr(e)
            )


            flash(
                "Something went wrong during registration.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        finally:

            if cursor:

                cursor.close()

            if connection:

                connection.close()


    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )


        # =====================================================
        # BASIC LOGIN VALIDATION
        # =====================================================

        if not email or not password:

            flash(
                "Email and password are required.",
                "error"
            )

            return redirect(
                url_for("auth.login")
            )


        if len(email) > 100 or not re.match(
            EMAIL_PATTERN,
            email
        ):

            flash(
                "Please enter a valid email address.",
                "error"
            )

            return redirect(
                url_for("auth.login")
            )


        connection = None
        cursor = None


        try:

            connection = get_db_connection()

            cursor = connection.cursor(
                dictionary=True
            )


            # =================================================
            # FIND USER BY EMAIL
            # =================================================

            cursor.execute(
                """
                SELECT
                    user_id,
                    full_name,
                    email,
                    password,
                    role,
                    status
                FROM users
                WHERE email = %s
                """,
                (email,)
            )


            user = cursor.fetchone()


            # =================================================
            # USER DOES NOT EXIST
            # =================================================

            if not user:

                flash(
                    "Invalid email or password.",
                    "error"
                )

                return redirect(
                    url_for("auth.login")
                )


            # =================================================
            # CHECK ACCOUNT STATUS
            # =================================================

            if user["status"] != "active":

                flash(
                    "Your account is not active.",
                    "error"
                )

                return redirect(
                    url_for("auth.login")
                )


            # =================================================
            # CHECK PASSWORD
            # =================================================

            if not check_password_hash(
                user["password"],
                password
            ):

                flash(
                    "Invalid email or password.",
                    "error"
                )

                return redirect(
                    url_for("auth.login")
                )


            # =================================================
            # LOGIN SUCCESSFUL
            # =================================================

            session["user_id"] = user["user_id"]

            session["full_name"] = user["full_name"]

            session["email"] = user["email"]

            session["role"] = user["role"]


            print(
                "LOGIN SUCCESS:",
                user["email"],
                user["role"]
            )


            # =================================================
            # REDIRECT TO DASHBOARD
            # =================================================

            return redirect(
                url_for("dashboard.dashboard_home")
            )


        except Exception as e:

            print(
                "LOGIN ERROR:",
                repr(e)
            )


            flash(
                "Something went wrong during login.",
                "error"
            )

            return redirect(
                url_for("auth.login")
            )


        finally:

            if cursor:

                cursor.close()

            if connection:

                connection.close()


    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@auth.route("/logout")
def logout():

    session.clear()


    flash(
        "You have been logged out successfully.",
        "success"
    )


    return redirect(
        url_for("auth.login")
    )