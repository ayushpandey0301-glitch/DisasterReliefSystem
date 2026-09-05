from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    flash,
    request
)

from werkzeug.security import check_password_hash, generate_password_hash

from utils.database import get_db_connection


settings = Blueprint("settings", __name__)


# =========================================================
# SETTINGS HOME
# =========================================================

@settings.route("/settings")
def settings_home():

    if "user_id" not in session:

        flash(
            "Please login first.",
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

        # -------------------------------------------------
        # GET NOTIFICATION PREFERENCES
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                relief_request_notifications,
                disaster_alerts,
                low_stock_alerts,
                vehicle_alerts,
                volunteer_updates,
                email_notifications
            FROM notification_preferences
            WHERE user_id = %s
            """,
            (
                session["user_id"],
            )
        )

        notification_preferences = cursor.fetchone()

        # -------------------------------------------------
        # CREATE DEFAULT PREFERENCES FOR NEW USER
        # -------------------------------------------------

        if not notification_preferences:

            cursor.execute(
                """
                INSERT INTO notification_preferences (
                    user_id,
                    relief_request_notifications,
                    disaster_alerts,
                    low_stock_alerts,
                    vehicle_alerts,
                    volunteer_updates,
                    email_notifications
                )
                VALUES (
                    %s,
                    TRUE,
                    TRUE,
                    TRUE,
                    TRUE,
                    TRUE,
                    FALSE
                )
                """,
                (
                    session["user_id"],
                )
            )

            connection.commit()

            notification_preferences = {
                "relief_request_notifications": 1,
                "disaster_alerts": 1,
                "low_stock_alerts": 1,
                "vehicle_alerts": 1,
                "volunteer_updates": 1,
                "email_notifications": 0
            }

        return render_template(
            "settings/settings.html",
            notification_preferences=notification_preferences
        )

    except Exception as e:

        print(
            "Settings Load Error:",
            e
        )

        flash(
            "Unable to load notification preferences.",
            "error"
        )

        return render_template(
            "settings/settings.html",
            notification_preferences={
                "relief_request_notifications": 1,
                "disaster_alerts": 1,
                "low_stock_alerts": 1,
                "vehicle_alerts": 1,
                "volunteer_updates": 1,
                "email_notifications": 0
            }
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# CHANGE PASSWORD
# =========================================================

@settings.route("/settings/change-password", methods=["POST"])
def change_password():

    if "user_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )

    current_password = request.form.get(
        "current_password",
        ""
    ).strip()

    new_password = request.form.get(
        "new_password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )

    # -----------------------------------------------------
    # BASIC VALIDATION
    # -----------------------------------------------------

    if not current_password:

        flash(
            "Please enter your current password.",
            "error"
        )

        return redirect(
            url_for("settings.settings_home")
        )

    if not new_password:

        flash(
            "Please enter a new password.",
            "error"
        )

        return redirect(
            url_for("settings.settings_home")
        )

    if not confirm_password:

        flash(
            "Please confirm your new password.",
            "error"
        )

        return redirect(
            url_for("settings.settings_home")
        )

    if len(new_password) < 8:

        flash(
            "New password must be at least 8 characters long.",
            "error"
        )

        return redirect(
            url_for("settings.settings_home")
        )

    if new_password != confirm_password:

        flash(
            "New password and confirm password do not match.",
            "error"
        )

        return redirect(
            url_for("settings.settings_home")
        )

    if current_password == new_password:

        flash(
            "New password must be different from your current password.",
            "error"
        )

        return redirect(
            url_for("settings.settings_home")
        )

    # -----------------------------------------------------
    # DATABASE OPERATION
    # -----------------------------------------------------

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                user_id,
                password
            FROM users
            WHERE user_id = %s
            """,
            (
                session["user_id"],
            )
        )

        user = cursor.fetchone()

        if not user:

            flash(
                "User account could not be found.",
                "error"
            )

            return redirect(
                url_for("settings.settings_home")
            )

        # -------------------------------------------------
        # CHECK CURRENT PASSWORD
        # -------------------------------------------------

        if not check_password_hash(
            user["password"],
            current_password
        ):

            flash(
                "Current password is incorrect.",
                "error"
            )

            return redirect(
                url_for("settings.settings_home")
            )

        # -------------------------------------------------
        # HASH NEW PASSWORD
        # -------------------------------------------------

        hashed_password = generate_password_hash(
            new_password
        )

        # -------------------------------------------------
        # UPDATE PASSWORD
        # -------------------------------------------------

        cursor.execute(
            """
            UPDATE users
            SET password = %s
            WHERE user_id = %s
            """,
            (
                hashed_password,
                session["user_id"]
            )
        )

        connection.commit()

        flash(
            "Password changed successfully.",
            "success"
        )

        return redirect(
            url_for("settings.settings_home")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "Change Password Error:",
            e
        )

        flash(
            "Something went wrong while changing your password.",
            "error"
        )

        return redirect(
            url_for("settings.settings_home")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# UPDATE NOTIFICATION PREFERENCES
# =========================================================

@settings.route(
    "/settings/notification-preferences",
    methods=["POST"]
)
def update_notification_preferences():

    if "user_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # CHECKBOX VALUES
    # -----------------------------------------------------

    relief_request_notifications = (
        1
        if request.form.get("relief_request_notifications")
        else 0
    )

    disaster_alerts = (
        1
        if request.form.get("disaster_alerts")
        else 0
    )

    low_stock_alerts = (
        1
        if request.form.get("low_stock_alerts")
        else 0
    )

    vehicle_alerts = (
        1
        if request.form.get("vehicle_alerts")
        else 0
    )

    volunteer_updates = (
        1
        if request.form.get("volunteer_updates")
        else 0
    )

    email_notifications = (
        1
        if request.form.get("email_notifications")
        else 0
    )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        # -------------------------------------------------
        # UPDATE EXISTING PREFERENCES
        # -------------------------------------------------

        cursor.execute(
            """
            UPDATE notification_preferences
            SET
                relief_request_notifications = %s,
                disaster_alerts = %s,
                low_stock_alerts = %s,
                vehicle_alerts = %s,
                volunteer_updates = %s,
                email_notifications = %s
            WHERE user_id = %s
            """,
            (
                relief_request_notifications,
                disaster_alerts,
                low_stock_alerts,
                vehicle_alerts,
                volunteer_updates,
                email_notifications,
                session["user_id"]
            )
        )

        # -------------------------------------------------
        # CREATE PREFERENCES IF THEY DON'T EXIST
        # -------------------------------------------------

        if cursor.rowcount == 0:

            cursor.execute(
                """
                INSERT INTO notification_preferences (
                    user_id,
                    relief_request_notifications,
                    disaster_alerts,
                    low_stock_alerts,
                    vehicle_alerts,
                    volunteer_updates,
                    email_notifications
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    session["user_id"],
                    relief_request_notifications,
                    disaster_alerts,
                    low_stock_alerts,
                    vehicle_alerts,
                    volunteer_updates,
                    email_notifications
                )
            )

        connection.commit()

        flash(
            "Notification preferences saved successfully.",
            "success"
        )

        return redirect(
            url_for("settings.settings_home")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "Notification Preferences Error:",
            e
        )

        flash(
            "Something went wrong while saving notification preferences.",
            "error"
        )

        return redirect(
            url_for("settings.settings_home")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

