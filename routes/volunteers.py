from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from utils.database import get_db_connection
import re


volunteers = Blueprint("volunteers", __name__)


# =========================================================
# VALIDATION OPTIONS
# =========================================================

VALID_STATUSES = {
    "active",
    "inactive"
}


# =========================================================
# ROLE HELPER
# =========================================================

def get_user_role():

    return str(
        session.get("role", "")
    ).strip().lower()


# =========================================================
# VOLUNTEER LIST
# =========================================================

@volunteers.route("/volunteers")
def volunteer_list():

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                user_id,
                full_name,
                email,
                phone,
                role,
                status,
                created_at
            FROM users
            WHERE role = 'volunteer'
            ORDER BY created_at DESC
        """)

        volunteers_list = cursor.fetchall()

        return render_template(
            "volunteers/list.html",
            volunteers=volunteers_list
        )

    except Exception as e:

        print(
            "VOLUNTEER LIST ERROR:",
            repr(e)
        )

        flash(
            "Unable to load volunteer records.",
            "error"
        )

        return redirect(
            url_for("dashboard.dashboard_home")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# VOLUNTEER DETAILS
# =========================================================

@volunteers.route("/volunteers/<int:user_id>")
def volunteer_details(user_id):

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                user_id,
                full_name,
                email,
                phone,
                status,
                created_at
            FROM users
            WHERE user_id = %s
              AND role = 'volunteer'
        """, (user_id,))

        volunteer = cursor.fetchone()

        if not volunteer:

            flash(
                "Volunteer not found.",
                "error"
            )

            return redirect(
                url_for("volunteers.volunteer_list")
            )

        return render_template(
            "volunteers/details.html",
            volunteer=volunteer
        )

    except Exception as e:

        print(
            "VOLUNTEER DETAILS ERROR:",
            repr(e)
        )

        flash(
            "Unable to load volunteer details.",
            "error"
        )

        return redirect(
            url_for("volunteers.volunteer_list")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# ADD VOLUNTEER
# ADMIN + COORDINATOR ONLY
# =========================================================

@volunteers.route(
    "/volunteers/add",
    methods=["GET", "POST"]
)
def add_volunteer():

    if "user_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )


    # =====================================================
    # ROLE CHECK
    # =====================================================

    user_role = get_user_role()

    if user_role not in {"admin", "coordinator"}:

        flash(
            "Only administrators and coordinators can add volunteers.",
            "error"
        )

        return redirect(
            url_for("volunteers.volunteer_list")
        )


    if request.method == "POST":

        # -------------------------------------------------
        # GET FORM DATA SAFELY
        # -------------------------------------------------

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        status = request.form.get(
            "status",
            "active"
        ).strip()


        # -------------------------------------------------
        # REQUIRED FIELD VALIDATION
        # -------------------------------------------------

        if not full_name or not email or not password:

            flash(
                "Name, email and password are required.",
                "error"
            )

            return redirect(
                url_for("volunteers.add_volunteer")
            )


        # -------------------------------------------------
        # FULL NAME VALIDATION
        # -------------------------------------------------

        if len(full_name) < 2:

            flash(
                "Volunteer name must contain at least 2 characters.",
                "error"
            )

            return redirect(
                url_for("volunteers.add_volunteer")
            )


        if len(full_name) > 100:

            flash(
                "Volunteer name cannot exceed 100 characters.",
                "error"
            )

            return redirect(
                url_for("volunteers.add_volunteer")
            )


        # -------------------------------------------------
        # EMAIL VALIDATION
        # -------------------------------------------------

        email_pattern = (
            r"^[A-Za-z0-9._%+-]+@"
            r"[A-Za-z0-9.-]+\."
            r"[A-Za-z]{2,}$"
        )

        if not re.fullmatch(
            email_pattern,
            email
        ):

            flash(
                "Please enter a valid email address.",
                "error"
            )

            return redirect(
                url_for("volunteers.add_volunteer")
            )


        if len(email) > 100:

            flash(
                "Email cannot exceed 100 characters.",
                "error"
            )

            return redirect(
                url_for("volunteers.add_volunteer")
            )


        # -------------------------------------------------
        # PASSWORD VALIDATION
        # -------------------------------------------------

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "error"
            )

            return redirect(
                url_for("volunteers.add_volunteer")
            )


        if len(password) > 255:

            flash(
                "Password cannot exceed 255 characters.",
                "error"
            )

            return redirect(
                url_for("volunteers.add_volunteer")
            )


        # -------------------------------------------------
        # PHONE VALIDATION
        # -------------------------------------------------

        if phone:

            if not phone.isdigit():

                flash(
                    "Phone number must contain only digits.",
                    "error"
                )

                return redirect(
                    url_for("volunteers.add_volunteer")
                )


            if len(phone) < 7 or len(phone) > 15:

                flash(
                    "Phone number must contain between 7 and 15 digits.",
                    "error"
                )

                return redirect(
                    url_for("volunteers.add_volunteer")
                )


        # -------------------------------------------------
        # STATUS VALIDATION
        # -------------------------------------------------

        if status not in VALID_STATUSES:

            flash(
                "Invalid volunteer status selected.",
                "error"
            )

            return redirect(
                url_for("volunteers.add_volunteer")
            )


        # -------------------------------------------------
        # HASH PASSWORD
        # -------------------------------------------------

        hashed_password = generate_password_hash(
            password
        )


        # -------------------------------------------------
        # DATABASE INSERT
        # -------------------------------------------------

        connection = None
        cursor = None

        try:

            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute("""
                SELECT
                    user_id
                FROM users
                WHERE email = %s
            """, (email,))

            existing_volunteer = cursor.fetchone()

            if existing_volunteer:

                flash(
                    "This email address is already registered.",
                    "error"
                )

                return redirect(
                    url_for("volunteers.add_volunteer")
                )


            cursor.execute("""
                INSERT INTO users
                (
                    full_name,
                    email,
                    password,
                    role,
                    phone,
                    status
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    'volunteer',
                    %s,
                    %s
                )
            """, (
                full_name,
                email,
                hashed_password,
                phone or None,
                status
            ))

            connection.commit()

            flash(
                "Volunteer added successfully.",
                "success"
            )

            return redirect(
                url_for("volunteers.volunteer_list")
            )

        except Exception as e:

            if connection:
                connection.rollback()

            print(
                "ADD VOLUNTEER ERROR:",
                repr(e)
            )

            if "Duplicate entry" in str(e):

                flash(
                    "This email address is already registered.",
                    "error"
                )

            else:

                flash(
                    "Unable to add volunteer.",
                    "error"
                )

            return redirect(
                url_for("volunteers.add_volunteer")
            )

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()


    return render_template(
        "volunteers/add.html"
    )


# =========================================================
# EDIT VOLUNTEER
# ADMIN + COORDINATOR ONLY
# =========================================================

@volunteers.route(
    "/volunteers/<int:user_id>/edit",
    methods=["GET", "POST"]
)
def edit_volunteer(user_id):

    if "user_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )


    # =====================================================
    # ROLE CHECK
    # =====================================================

    user_role = get_user_role()

    if user_role not in {"admin", "coordinator"}:

        flash(
            "Only administrators and coordinators can edit volunteers.",
            "error"
        )

        return redirect(
            url_for("volunteers.volunteer_list")
        )


    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                user_id,
                full_name,
                email,
                phone,
                status
            FROM users
            WHERE user_id = %s
              AND role = 'volunteer'
        """, (user_id,))

        volunteer = cursor.fetchone()

        if not volunteer:

            flash(
                "Volunteer not found.",
                "error"
            )

            return redirect(
                url_for("volunteers.volunteer_list")
            )


        # =================================================
        # UPDATE VOLUNTEER
        # =================================================

        if request.method == "POST":

            full_name = request.form.get(
                "full_name",
                ""
            ).strip()

            email = request.form.get(
                "email",
                ""
            ).strip()

            phone = request.form.get(
                "phone",
                ""
            ).strip()

            status = request.form.get(
                "status",
                "active"
            ).strip()


            # -------------------------------------------------
            # REQUIRED FIELD VALIDATION
            # -------------------------------------------------

            if not full_name or not email:

                flash(
                    "Name and email are required.",
                    "error"
                )

                return redirect(
                    url_for(
                        "volunteers.edit_volunteer",
                        user_id=user_id
                    )
                )


            # -------------------------------------------------
            # FULL NAME VALIDATION
            # -------------------------------------------------

            if len(full_name) < 2:

                flash(
                    "Volunteer name must contain at least 2 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "volunteers.edit_volunteer",
                        user_id=user_id
                    )
                )


            if len(full_name) > 100:

                flash(
                    "Volunteer name cannot exceed 100 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "volunteers.edit_volunteer",
                        user_id=user_id
                    )
                )


            # -------------------------------------------------
            # EMAIL VALIDATION
            # -------------------------------------------------

            email_pattern = (
                r"^[A-Za-z0-9._%+-]+@"
                r"[A-Za-z0-9.-]+\."
                r"[A-Za-z]{2,}$"
            )

            if not re.fullmatch(
                email_pattern,
                email
            ):

                flash(
                    "Please enter a valid email address.",
                    "error"
                )

                return redirect(
                    url_for(
                        "volunteers.edit_volunteer",
                        user_id=user_id
                    )
                )


            if len(email) > 100:

                flash(
                    "Email cannot exceed 100 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "volunteers.edit_volunteer",
                        user_id=user_id
                    )
                )


            # -------------------------------------------------
            # PHONE VALIDATION
            # -------------------------------------------------

            if phone:

                if not phone.isdigit():

                    flash(
                        "Phone number must contain only digits.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "volunteers.edit_volunteer",
                            user_id=user_id
                        )
                    )


                if len(phone) < 7 or len(phone) > 15:

                    flash(
                        "Phone number must contain between 7 and 15 digits.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "volunteers.edit_volunteer",
                            user_id=user_id
                        )
                    )


            # -------------------------------------------------
            # STATUS VALIDATION
            # -------------------------------------------------

            if status not in VALID_STATUSES:

                flash(
                    "Invalid volunteer status selected.",
                    "error"
                )

                return redirect(
                    url_for(
                        "volunteers.edit_volunteer",
                        user_id=user_id
                    )
                )


            # -------------------------------------------------
            # CHECK DUPLICATE EMAIL
            # -------------------------------------------------

            cursor.execute("""
                SELECT
                    user_id
                FROM users
                WHERE email = %s
                  AND user_id != %s
            """, (
                email,
                user_id
            ))

            existing_volunteer = cursor.fetchone()

            if existing_volunteer:

                flash(
                    "This email address is already registered.",
                    "error"
                )

                return redirect(
                    url_for(
                        "volunteers.edit_volunteer",
                        user_id=user_id
                    )
                )


            # -------------------------------------------------
            # DATABASE UPDATE
            # -------------------------------------------------

            cursor.execute("""
                UPDATE users
                SET
                    full_name = %s,
                    email = %s,
                    phone = %s,
                    status = %s
                WHERE user_id = %s
                  AND role = 'volunteer'
            """, (
                full_name,
                email,
                phone or None,
                status,
                user_id
            ))

            connection.commit()

            flash(
                "Volunteer updated successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "volunteers.volunteer_details",
                    user_id=user_id
                )
            )


        return render_template(
            "volunteers/edit.html",
            volunteer=volunteer
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "EDIT VOLUNTEER ERROR:",
            repr(e)
        )

        if "Duplicate entry" in str(e):

            flash(
                "This email address is already registered.",
                "error"
            )

        else:

            flash(
                "Unable to update volunteer.",
                "error"
            )

        return redirect(
            url_for("volunteers.volunteer_list")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# DELETE VOLUNTEER
# ADMIN ONLY
# =========================================================

@volunteers.route(
    "/volunteers/delete/<int:user_id>",
    methods=["POST"]
)
def delete_volunteer(user_id):

    # =====================================================
    # LOGIN CHECK
    # =====================================================

    if "user_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )


    # =====================================================
    # ADMIN ONLY CHECK
    # =====================================================

    user_role = get_user_role()

    if user_role != "admin":

        flash(
            "Only administrators can delete volunteers.",
            "error"
        )

        return redirect(
            url_for("volunteers.volunteer_list")
        )


    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()


        # -------------------------------------------------
        # CHECK VOLUNTEER EXISTS
        # -------------------------------------------------

        cursor.execute("""
            SELECT user_id
            FROM users
            WHERE user_id = %s
              AND role = 'volunteer'
        """, (user_id,))

        volunteer = cursor.fetchone()

        if not volunteer:

            flash(
                "Volunteer not found.",
                "error"
            )

            return redirect(
                url_for("volunteers.volunteer_list")
            )


        # -------------------------------------------------
        # DELETE VOLUNTEER
        # -------------------------------------------------

        cursor.execute("""
            DELETE FROM users
            WHERE user_id = %s
              AND role = 'volunteer'
        """, (user_id,))

        connection.commit()

        flash(
            "Volunteer deleted successfully.",
            "success"
        )


    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "DELETE VOLUNTEER ERROR:",
            repr(e)
        )

        flash(
            "Unable to delete volunteer.",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


    return redirect(
        url_for("volunteers.volunteer_list")
    )