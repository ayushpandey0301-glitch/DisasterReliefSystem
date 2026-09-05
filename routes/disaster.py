from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.database import get_db_connection
from datetime import datetime


disaster = Blueprint("disaster", __name__)


# =========================================================
# VALIDATION OPTIONS
# =========================================================

VALID_DISASTER_TYPES = {
    "Flood",
    "Earthquake",
    "Cyclone",
    "Landslide",
    "Fire",
    "Drought",
    "Tsunami",
    "Other"
}

VALID_SEVERITIES = {
    "Low",
    "Medium",
    "High",
    "Critical"
}

VALID_STATUSES = {
    "Active",
    "Resolved",
    "Closed"
}


# =========================================================
# DISASTER LIST
# =========================================================

@disaster.route("/disasters")
def disaster_list():

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
                disaster_id,
                disaster_name,
                disaster_type,
                description,
                location,
                severity,
                start_date,
                end_date,
                status,
                created_at
            FROM disasters
            ORDER BY created_at DESC
        """)

        disasters = cursor.fetchall()

        return render_template(
            "disasters/list.html",
            disasters=disasters
        )

    except Exception as e:

        print(
            "DISASTER LIST ERROR:",
            repr(e)
        )

        flash(
            "Unable to load disaster records.",
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
# DISASTER DETAILS
# =========================================================

@disaster.route("/disasters/<int:disaster_id>")
def disaster_details(disaster_id):

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
                disaster_id,
                disaster_name,
                disaster_type,
                description,
                location,
                severity,
                start_date,
                end_date,
                status,
                created_at
            FROM disasters
            WHERE disaster_id = %s
        """, (disaster_id,))

        disaster_record = cursor.fetchone()

        if not disaster_record:

            flash(
                "Disaster not found.",
                "error"
            )

            return redirect(
                url_for("disaster.disaster_list")
            )

        return render_template(
            "disasters/details.html",
            disaster=disaster_record
        )

    except Exception as e:

        print(
            "DISASTER DETAILS ERROR:",
            repr(e)
        )

        flash(
            "Unable to load disaster details.",
            "error"
        )

        return redirect(
            url_for("disaster.disaster_list")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# ADD DISASTER
# =========================================================

@disaster.route(
    "/disasters/add",
    methods=["GET", "POST"]
)
def add_disaster():

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        # -------------------------------------------------
        # GET FORM DATA SAFELY
        # -------------------------------------------------

        disaster_name = request.form.get(
            "disaster_name",
            ""
        ).strip()

        disaster_type = request.form.get(
            "disaster_type",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        severity = request.form.get(
            "severity",
            ""
        ).strip()

        start_date = request.form.get(
            "start_date",
            ""
        ).strip()

        end_date = request.form.get(
            "end_date",
            ""
        ).strip() or None

        status = request.form.get(
            "status",
            ""
        ).strip()


        # -------------------------------------------------
        # REQUIRED FIELD VALIDATION
        # -------------------------------------------------

        if (
            not disaster_name
            or not disaster_type
            or not description
            or not location
            or not severity
            or not start_date
            or not status
        ):

            flash(
                "Please fill in all required fields.",
                "error"
            )

            return redirect(
                url_for("disaster.add_disaster")
            )


        # -------------------------------------------------
        # DISASTER NAME VALIDATION
        # -------------------------------------------------

        if len(disaster_name) < 3:

            flash(
                "Disaster name must contain at least 3 characters.",
                "error"
            )

            return redirect(
                url_for("disaster.add_disaster")
            )


        if len(disaster_name) > 150:

            flash(
                "Disaster name cannot exceed 150 characters.",
                "error"
            )

            return redirect(
                url_for("disaster.add_disaster")
            )


        # -------------------------------------------------
        # DESCRIPTION VALIDATION
        # -------------------------------------------------

        if len(description) < 10:

            flash(
                "Description must contain at least 10 characters.",
                "error"
            )

            return redirect(
                url_for("disaster.add_disaster")
            )


        if len(description) > 1000:

            flash(
                "Description cannot exceed 1000 characters.",
                "error"
            )

            return redirect(
                url_for("disaster.add_disaster")
            )


        # -------------------------------------------------
        # LOCATION VALIDATION
        # -------------------------------------------------

        if len(location) < 2:

            flash(
                "Location must contain at least 2 characters.",
                "error"
            )

            return redirect(
                url_for("disaster.add_disaster")
            )


        if len(location) > 255:

            flash(
                "Location cannot exceed 255 characters.",
                "error"
            )

            return redirect(
                url_for("disaster.add_disaster")
            )


        # -------------------------------------------------
        # DISASTER TYPE VALIDATION
        # -------------------------------------------------

        if disaster_type not in VALID_DISASTER_TYPES:

            flash(
                "Invalid disaster type selected.",
                "error"
            )

            return redirect(
                url_for("disaster.add_disaster")
            )


        # -------------------------------------------------
        # SEVERITY VALIDATION
        # -------------------------------------------------

        if severity not in VALID_SEVERITIES:

            flash(
                "Invalid severity selected.",
                "error"
            )

            return redirect(
                url_for("disaster.add_disaster")
            )


        # -------------------------------------------------
        # STATUS VALIDATION
        # -------------------------------------------------

        if status not in VALID_STATUSES:

            flash(
                "Invalid disaster status selected.",
                "error"
            )

            return redirect(
                url_for("disaster.add_disaster")
            )


        # -------------------------------------------------
        # DATE VALIDATION
        # -------------------------------------------------

        try:

            start_date_obj = datetime.strptime(
                start_date,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            flash(
                "Invalid start date.",
                "error"
            )

            return redirect(
                url_for("disaster.add_disaster")
            )


        if end_date:

            try:

                end_date_obj = datetime.strptime(
                    end_date,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "Invalid end date.",
                    "error"
                )

                return redirect(
                    url_for("disaster.add_disaster")
                )


            if end_date_obj < start_date_obj:

                flash(
                    "End date cannot be before the start date.",
                    "error"
                )

                return redirect(
                    url_for("disaster.add_disaster")
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
                INSERT INTO disasters
                (
                    disaster_name,
                    disaster_type,
                    description,
                    location,
                    severity,
                    start_date,
                    end_date,
                    status,
                    created_by
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                disaster_name,
                disaster_type,
                description,
                location,
                severity,
                start_date,
                end_date,
                status,
                session["user_id"]
            ))

            connection.commit()

            flash(
                "Disaster added successfully.",
                "success"
            )

            return redirect(
                url_for("disaster.disaster_list")
            )

        except Exception as e:

            if connection:
                connection.rollback()

            print(
                "ADD DISASTER ERROR:",
                repr(e)
            )

            flash(
                "Unable to add disaster.",
                "error"
            )

            return redirect(
                url_for("disaster.add_disaster")
            )

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template(
        "disasters/add.html"
    )


# =========================================================
# EDIT DISASTER
# =========================================================

@disaster.route(
    "/disasters/<int:disaster_id>/edit",
    methods=["GET", "POST"]
)
def edit_disaster(disaster_id):

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # -------------------------------------------------
        # GET EXISTING DISASTER
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                disaster_id,
                disaster_name,
                disaster_type,
                description,
                location,
                severity,
                start_date,
                end_date,
                status
            FROM disasters
            WHERE disaster_id = %s
        """, (disaster_id,))

        disaster_record = cursor.fetchone()

        if not disaster_record:

            flash(
                "Disaster not found.",
                "error"
            )

            return redirect(
                url_for("disaster.disaster_list")
            )


        # -------------------------------------------------
        # UPDATE DISASTER
        # -------------------------------------------------

        if request.method == "POST":

            disaster_name = request.form.get(
                "disaster_name",
                ""
            ).strip()

            disaster_type = request.form.get(
                "disaster_type",
                ""
            ).strip()

            description = request.form.get(
                "description",
                ""
            ).strip()

            location = request.form.get(
                "location",
                ""
            ).strip()

            severity = request.form.get(
                "severity",
                ""
            ).strip()

            start_date = request.form.get(
                "start_date",
                ""
            ).strip()

            end_date = request.form.get(
                "end_date",
                ""
            ).strip() or None

            status = request.form.get(
                "status",
                ""
            ).strip()


            # -------------------------------------------------
            # REQUIRED FIELD VALIDATION
            # -------------------------------------------------

            if (
                not disaster_name
                or not disaster_type
                or not description
                or not location
                or not severity
                or not start_date
                or not status
            ):

                flash(
                    "Please fill in all required fields.",
                    "error"
                )

                return redirect(
                    url_for(
                        "disaster.edit_disaster",
                        disaster_id=disaster_id
                    )
                )


            # -------------------------------------------------
            # TEXT VALIDATION
            # -------------------------------------------------

            if len(disaster_name) < 3:

                flash(
                    "Disaster name must contain at least 3 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "disaster.edit_disaster",
                        disaster_id=disaster_id
                    )
                )


            if len(disaster_name) > 150:

                flash(
                    "Disaster name cannot exceed 150 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "disaster.edit_disaster",
                        disaster_id=disaster_id
                    )
                )


            if len(description) < 10:

                flash(
                    "Description must contain at least 10 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "disaster.edit_disaster",
                        disaster_id=disaster_id
                    )
                )


            if len(description) > 1000:

                flash(
                    "Description cannot exceed 1000 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "disaster.edit_disaster",
                        disaster_id=disaster_id
                    )
                )


            if len(location) < 2:

                flash(
                    "Location must contain at least 2 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "disaster.edit_disaster",
                        disaster_id=disaster_id
                    )
                )


            if len(location) > 255:

                flash(
                    "Location cannot exceed 255 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "disaster.edit_disaster",
                        disaster_id=disaster_id
                    )
                )


            # -------------------------------------------------
            # SELECT VALIDATION
            # -------------------------------------------------

            if disaster_type not in VALID_DISASTER_TYPES:

                flash(
                    "Invalid disaster type selected.",
                    "error"
                )

                return redirect(
                    url_for(
                        "disaster.edit_disaster",
                        disaster_id=disaster_id
                    )
                )


            if severity not in VALID_SEVERITIES:

                flash(
                    "Invalid severity selected.",
                    "error"
                )

                return redirect(
                    url_for(
                        "disaster.edit_disaster",
                        disaster_id=disaster_id
                    )
                )


            if status not in VALID_STATUSES:

                flash(
                    "Invalid disaster status selected.",
                    "error"
                )

                return redirect(
                    url_for(
                        "disaster.edit_disaster",
                        disaster_id=disaster_id
                    )
                )


            # -------------------------------------------------
            # DATE VALIDATION
            # -------------------------------------------------

            try:

                start_date_obj = datetime.strptime(
                    start_date,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "Invalid start date.",
                    "error"
                )

                return redirect(
                    url_for(
                        "disaster.edit_disaster",
                        disaster_id=disaster_id
                    )
                )


            if end_date:

                try:

                    end_date_obj = datetime.strptime(
                        end_date,
                        "%Y-%m-%d"
                    ).date()

                except ValueError:

                    flash(
                        "Invalid end date.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "disaster.edit_disaster",
                            disaster_id=disaster_id
                        )
                    )


                if end_date_obj < start_date_obj:

                    flash(
                        "End date cannot be before the start date.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "disaster.edit_disaster",
                            disaster_id=disaster_id
                        )
                    )


            # -------------------------------------------------
            # DATABASE UPDATE
            # -------------------------------------------------

            cursor.execute("""
                UPDATE disasters
                SET
                    disaster_name = %s,
                    disaster_type = %s,
                    description = %s,
                    location = %s,
                    severity = %s,
                    start_date = %s,
                    end_date = %s,
                    status = %s
                WHERE disaster_id = %s
            """, (
                disaster_name,
                disaster_type,
                description,
                location,
                severity,
                start_date,
                end_date,
                status,
                disaster_id
            ))

            connection.commit()

            flash(
                "Disaster updated successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "disaster.disaster_details",
                    disaster_id=disaster_id
                )
            )

        return render_template(
            "disasters/edit.html",
            disaster=disaster_record
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "EDIT DISASTER ERROR:",
            repr(e)
        )

        flash(
            "Unable to update disaster.",
            "error"
        )

        return redirect(
            url_for(
                "disaster.disaster_details",
                disaster_id=disaster_id
            )
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# DELETE DISASTER
# =========================================================

@disaster.route(
    "/disasters/delete/<int:disaster_id>",
    methods=["POST"]
)
def delete_disaster(disaster_id):

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        # -------------------------------------------------
        # CHECK WHETHER DISASTER EXISTS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                disaster_id
            FROM disasters
            WHERE disaster_id = %s
        """, (disaster_id,))

        disaster_record = cursor.fetchone()

        if not disaster_record:

            flash(
                "Disaster not found.",
                "error"
            )

            return redirect(
                url_for("disaster.disaster_list")
            )

        # -------------------------------------------------
        # DATABASE DELETE
        # -------------------------------------------------

        cursor.execute("""
            DELETE FROM disasters
            WHERE disaster_id = %s
        """, (disaster_id,))

        connection.commit()

        flash(
            "Disaster deleted successfully.",
            "success"
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "DELETE DISASTER ERROR:",
            repr(e)
        )

        flash(
            "Unable to delete disaster.",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

    return redirect(
        url_for("disaster.disaster_list")
    )