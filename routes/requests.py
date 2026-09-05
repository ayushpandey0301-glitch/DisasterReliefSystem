from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.database import get_db_connection


requests = Blueprint("requests", __name__)


# =========================================================
# VALIDATION OPTIONS
# =========================================================

VALID_REQUEST_TYPES = {
    "Food",
    "Water",
    "Medicine",
    "Clothing",
    "Shelter",
    "Rescue",
    "Other"
}

VALID_PRIORITIES = {
    "Low",
    "Medium",
    "High",
    "Critical"
}

VALID_STATUSES = {
    "Pending",
    "In Progress",
    "Resolved",
    "Rejected"
}


# =========================================================
# RELIEF REQUEST LIST
# =========================================================

@requests.route("/requests")
def request_list():

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
                request_id,
                requester_name,
                contact,
                request_type,
                description,
                location,
                priority,
                status,
                created_at
            FROM relief_requests
            ORDER BY created_at DESC
        """)

        requests_list = cursor.fetchall()

        return render_template(
            "requests/list.html",
            requests=requests_list
        )

    except Exception as e:

        print(
            "REQUEST LIST ERROR:",
            repr(e)
        )

        flash(
            "Unable to load relief requests.",
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
# RELIEF REQUEST DETAILS
# =========================================================

@requests.route("/requests/<int:request_id>")
def request_details(request_id):

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
                request_id,
                requester_name,
                contact,
                request_type,
                description,
                location,
                priority,
                status,
                created_at
            FROM relief_requests
            WHERE request_id = %s
        """, (request_id,))

        relief_request = cursor.fetchone()

        if not relief_request:

            flash(
                "Relief request not found.",
                "error"
            )

            return redirect(
                url_for("requests.request_list")
            )

        return render_template(
            "requests/details.html",
            request=relief_request
        )

    except Exception as e:

        print(
            "REQUEST DETAILS ERROR:",
            repr(e)
        )

        flash(
            "Unable to load relief request details.",
            "error"
        )

        return redirect(
            url_for("requests.request_list")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# ADD RELIEF REQUEST
# =========================================================

@requests.route(
    "/requests/add",
    methods=["GET", "POST"]
)
def add_request():

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        requester_name = request.form.get(
            "requester_name",
            ""
        ).strip()

        contact = request.form.get(
            "contact",
            ""
        ).strip()

        request_type = request.form.get(
            "request_type",
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

        priority = request.form.get(
            "priority",
            "Medium"
        ).strip()

        status = request.form.get(
            "status",
            "Pending"
        ).strip()

        # -------------------------------------------------
        # REQUIRED FIELD VALIDATION
        # -------------------------------------------------

        if not requester_name or not request_type or not location:

            flash(
                "Requester name, request type and location are required.",
                "error"
            )

            return redirect(
                url_for("requests.add_request")
            )

        # -------------------------------------------------
        # REQUESTER NAME VALIDATION
        # -------------------------------------------------

        if len(requester_name) < 2:

            flash(
                "Requester name must contain at least 2 characters.",
                "error"
            )

            return redirect(
                url_for("requests.add_request")
            )

        if len(requester_name) > 100:

            flash(
                "Requester name cannot exceed 100 characters.",
                "error"
            )

            return redirect(
                url_for("requests.add_request")
            )

        # -------------------------------------------------
        # CONTACT VALIDATION
        # -------------------------------------------------

        if contact:

            if not contact.isdigit():

                flash(
                    "Contact must contain only digits.",
                    "error"
                )

                return redirect(
                    url_for("requests.add_request")
                )

            if len(contact) < 7 or len(contact) > 15:

                flash(
                    "Contact must contain between 7 and 15 digits.",
                    "error"
                )

                return redirect(
                    url_for("requests.add_request")
                )

        # -------------------------------------------------
        # REQUEST TYPE VALIDATION
        # -------------------------------------------------

        if request_type not in VALID_REQUEST_TYPES:

            flash(
                "Invalid request type selected.",
                "error"
            )

            return redirect(
                url_for("requests.add_request")
            )

        # -------------------------------------------------
        # DESCRIPTION VALIDATION
        # -------------------------------------------------

        if len(description) > 1000:

            flash(
                "Description cannot exceed 1000 characters.",
                "error"
            )

            return redirect(
                url_for("requests.add_request")
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
                url_for("requests.add_request")
            )

        if len(location) > 255:

            flash(
                "Location cannot exceed 255 characters.",
                "error"
            )

            return redirect(
                url_for("requests.add_request")
            )

        # -------------------------------------------------
        # PRIORITY VALIDATION
        # -------------------------------------------------

        if priority not in VALID_PRIORITIES:

            flash(
                "Invalid priority selected.",
                "error"
            )

            return redirect(
                url_for("requests.add_request")
            )

        # -------------------------------------------------
        # STATUS VALIDATION
        # -------------------------------------------------

        if status not in VALID_STATUSES:

            flash(
                "Invalid request status selected.",
                "error"
            )

            return redirect(
                url_for("requests.add_request")
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
                INSERT INTO relief_requests
                (
                    requester_name,
                    contact,
                    request_type,
                    description,
                    location,
                    priority,
                    status
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                requester_name,
                contact or None,
                request_type,
                description or None,
                location,
                priority,
                status
            ))

            connection.commit()

            flash(
                "Relief request added successfully.",
                "success"
            )

            return redirect(
                url_for("requests.request_list")
            )

        except Exception as e:

            if connection:
                connection.rollback()

            print(
                "ADD REQUEST ERROR:",
                repr(e)
            )

            flash(
                "Unable to add relief request.",
                "error"
            )

            return redirect(
                url_for("requests.add_request")
            )

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template(
        "requests/add.html"
    )


# =========================================================
# EDIT RELIEF REQUEST
# =========================================================

@requests.route(
    "/requests/<int:request_id>/edit",
    methods=["GET", "POST"]
)
def edit_request(request_id):

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
                request_id,
                requester_name,
                contact,
                request_type,
                description,
                location,
                priority,
                status
            FROM relief_requests
            WHERE request_id = %s
        """, (request_id,))

        relief_request = cursor.fetchone()

        if not relief_request:

            flash(
                "Relief request not found.",
                "error"
            )

            return redirect(
                url_for("requests.request_list")
            )

        if request.method == "POST":

            requester_name = request.form.get(
                "requester_name",
                ""
            ).strip()

            contact = request.form.get(
                "contact",
                ""
            ).strip()

            request_type = request.form.get(
                "request_type",
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

            priority = request.form.get(
                "priority",
                "Medium"
            ).strip()

            status = request.form.get(
                "status",
                "Pending"
            ).strip()

            # -------------------------------------------------
            # REQUIRED FIELD VALIDATION
            # -------------------------------------------------

            if not requester_name or not request_type or not location:

                flash(
                    "Requester name, request type and location are required.",
                    "error"
                )

                return redirect(
                    url_for(
                        "requests.edit_request",
                        request_id=request_id
                    )
                )

            # -------------------------------------------------
            # REQUESTER NAME VALIDATION
            # -------------------------------------------------

            if len(requester_name) < 2:

                flash(
                    "Requester name must contain at least 2 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "requests.edit_request",
                        request_id=request_id
                    )
                )

            if len(requester_name) > 100:

                flash(
                    "Requester name cannot exceed 100 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "requests.edit_request",
                        request_id=request_id
                    )
                )

            # -------------------------------------------------
            # CONTACT VALIDATION
            # -------------------------------------------------

            if contact:

                if not contact.isdigit():

                    flash(
                        "Contact must contain only digits.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "requests.edit_request",
                            request_id=request_id
                        )
                    )

                if len(contact) < 7 or len(contact) > 15:

                    flash(
                        "Contact must contain between 7 and 15 digits.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "requests.edit_request",
                            request_id=request_id
                        )
                    )

            # -------------------------------------------------
            # REQUEST TYPE VALIDATION
            # -------------------------------------------------

            if request_type not in VALID_REQUEST_TYPES:

                flash(
                    "Invalid request type selected.",
                    "error"
                )

                return redirect(
                    url_for(
                        "requests.edit_request",
                        request_id=request_id
                    )
                )

            # -------------------------------------------------
            # DESCRIPTION VALIDATION
            # -------------------------------------------------

            if len(description) > 1000:

                flash(
                    "Description cannot exceed 1000 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "requests.edit_request",
                        request_id=request_id
                    )
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
                    url_for(
                        "requests.edit_request",
                        request_id=request_id
                    )
                )

            if len(location) > 255:

                flash(
                    "Location cannot exceed 255 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "requests.edit_request",
                        request_id=request_id
                    )
                )

            # -------------------------------------------------
            # PRIORITY VALIDATION
            # -------------------------------------------------

            if priority not in VALID_PRIORITIES:

                flash(
                    "Invalid priority selected.",
                    "error"
                )

                return redirect(
                    url_for(
                        "requests.edit_request",
                        request_id=request_id
                    )
                )

            # -------------------------------------------------
            # STATUS VALIDATION
            # -------------------------------------------------

            if status not in VALID_STATUSES:

                flash(
                    "Invalid request status selected.",
                    "error"
                )

                return redirect(
                    url_for(
                        "requests.edit_request",
                        request_id=request_id
                    )
                )

            # -------------------------------------------------
            # DATABASE UPDATE
            # -------------------------------------------------

            cursor.execute("""
                UPDATE relief_requests
                SET
                    requester_name = %s,
                    contact = %s,
                    request_type = %s,
                    description = %s,
                    location = %s,
                    priority = %s,
                    status = %s
                WHERE request_id = %s
            """, (
                requester_name,
                contact or None,
                request_type,
                description or None,
                location,
                priority,
                status,
                request_id
            ))

            connection.commit()

            flash(
                "Relief request updated successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "requests.request_details",
                    request_id=request_id
                )
            )

        return render_template(
            "requests/edit.html",
            request=relief_request
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "EDIT REQUEST ERROR:",
            repr(e)
        )

        flash(
            "Unable to update relief request.",
            "error"
        )

        return redirect(
            url_for("requests.request_list")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# DELETE RELIEF REQUEST
# =========================================================

@requests.route(
    "/requests/delete/<int:request_id>",
    methods=["POST"]
)
def delete_request(request_id):

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        # -------------------------------------------------
        # CHECK REQUEST EXISTS
        # -------------------------------------------------

        cursor.execute("""
            SELECT request_id
            FROM relief_requests
            WHERE request_id = %s
        """, (request_id,))

        relief_request = cursor.fetchone()

        if not relief_request:

            flash(
                "Relief request not found.",
                "error"
            )

            return redirect(
                url_for("requests.request_list")
            )

        # -------------------------------------------------
        # DELETE REQUEST
        # -------------------------------------------------

        cursor.execute("""
            DELETE FROM relief_requests
            WHERE request_id = %s
        """, (request_id,))

        connection.commit()

        flash(
            "Relief request deleted successfully.",
            "success"
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "DELETE REQUEST ERROR:",
            repr(e)
        )

        flash(
            "Unable to delete relief request.",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

    return redirect(
        url_for("requests.request_list")
    )