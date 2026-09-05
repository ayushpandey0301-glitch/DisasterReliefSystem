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
    "Approved",
    "Rejected",
    "Partially Allocated",
    "Completed"
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
                rr.request_id,
                rr.disaster_id,
                d.disaster_name,
                rr.requested_by,
                u.full_name AS requester_name,
                u.phone AS contact,
                rr.resource_type AS request_type,
                rr.resource_name,
                rr.quantity_requested,
                rr.reason AS description,
                rr.request_location AS location,
                rr.priority,
                rr.status,
                rr.requested_at AS created_at
            FROM resource_requests rr
            LEFT JOIN users u
                ON rr.requested_by = u.user_id
            LEFT JOIN disasters d
                ON rr.disaster_id = d.disaster_id
            ORDER BY rr.requested_at DESC
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
                rr.request_id,
                rr.disaster_id,
                d.disaster_name,
                rr.requested_by,
                u.full_name AS requester_name,
                u.phone AS contact,
                rr.resource_type AS request_type,
                rr.resource_name,
                rr.quantity_requested,
                rr.reason AS description,
                rr.request_location AS location,
                rr.priority,
                rr.status,
                rr.requested_at AS created_at
            FROM resource_requests rr
            LEFT JOIN users u
                ON rr.requested_by = u.user_id
            LEFT JOIN disasters d
                ON rr.disaster_id = d.disaster_id
            WHERE rr.request_id = %s
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

        disaster_id = request.form.get(
            "disaster_id",
            ""
        ).strip()

        request_type = request.form.get(
            "request_type",
            ""
        ).strip()

        resource_name = request.form.get(
            "resource_name",
            ""
        ).strip()

        quantity_requested = request.form.get(
            "quantity_requested",
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

        if (
            not disaster_id
            or not request_type
            or not resource_name
            or not quantity_requested
            or not location
        ):

            flash(
                "Disaster ID, resource type, resource name, quantity and location are required.",
                "error"
            )

            return redirect(
                url_for("requests.add_request")
            )

        # -------------------------------------------------
        # DISASTER ID VALIDATION
        # -------------------------------------------------

        if not disaster_id.isdigit():

            flash(
                "Disaster ID must be a valid number.",
                "error"
            )

            return redirect(
                url_for("requests.add_request")
            )

        disaster_id = int(disaster_id)

        if disaster_id <= 0:

            flash(
                "Disaster ID must be greater than 0.",
                "error"
            )

            return redirect(
                url_for("requests.add_request")
            )

        # -------------------------------------------------
        # RESOURCE TYPE VALIDATION
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
        # RESOURCE NAME VALIDATION
        # -------------------------------------------------

        if len(resource_name) < 2:

            flash(
                "Resource name must contain at least 2 characters.",
                "error"
            )

            return redirect(
                url_for("requests.add_request")
            )

        if len(resource_name) > 150:

            flash(
                "Resource name cannot exceed 150 characters.",
                "error"
            )

            return redirect(
                url_for("requests.add_request")
            )

        # -------------------------------------------------
        # QUANTITY VALIDATION
        # -------------------------------------------------

        if not quantity_requested.isdigit():

            flash(
                "Quantity must be a valid positive number.",
                "error"
            )

            return redirect(
                url_for("requests.add_request")
            )

        quantity_requested = int(quantity_requested)

        if quantity_requested <= 0:

            flash(
                "Quantity must be greater than 0.",
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

            # -------------------------------------------------
            # CHECK DISASTER EXISTS
            # -------------------------------------------------

            cursor.execute("""
                SELECT disaster_id
                FROM disasters
                WHERE disaster_id = %s
            """, (disaster_id,))

            disaster = cursor.fetchone()

            if not disaster:

                flash(
                    "Selected disaster does not exist.",
                    "error"
                )

                return redirect(
                    url_for("requests.add_request")
                )

            # -------------------------------------------------
            # INSERT REQUEST
            # -------------------------------------------------

            cursor.execute("""
                INSERT INTO resource_requests
                (
                    disaster_id,
                    requested_by,
                    resource_type,
                    resource_name,
                    quantity_requested,
                    priority,
                    request_location,
                    reason,
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
                    %s,
                    %s,
                    %s
                )
            """, (
                disaster_id,
                session["user_id"],
                request_type,
                resource_name,
                quantity_requested,
                priority,
                location,
                description or None,
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
                rr.request_id,
                rr.disaster_id,
                d.disaster_name,
                rr.requested_by,
                u.full_name AS requester_name,
                u.phone AS contact,
                rr.resource_type AS request_type,
                rr.resource_name,
                rr.quantity_requested,
                rr.reason AS description,
                rr.request_location AS location,
                rr.priority,
                rr.status
            FROM resource_requests rr
            LEFT JOIN users u
                ON rr.requested_by = u.user_id
            LEFT JOIN disasters d
                ON rr.disaster_id = d.disaster_id
            WHERE rr.request_id = %s
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

            disaster_id = request.form.get(
                "disaster_id",
                str(relief_request["disaster_id"])
            ).strip()

            request_type = request.form.get(
                "request_type",
                ""
            ).strip()

            resource_name = request.form.get(
                "resource_name",
                relief_request["resource_name"] or ""
            ).strip()

            quantity_requested = request.form.get(
                "quantity_requested",
                str(relief_request["quantity_requested"])
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

            if (
                not disaster_id
                or not request_type
                or not resource_name
                or not quantity_requested
                or not location
            ):

                flash(
                    "Disaster ID, resource type, resource name, quantity and location are required.",
                    "error"
                )

                return redirect(
                    url_for(
                        "requests.edit_request",
                        request_id=request_id
                    )
                )

            # -------------------------------------------------
            # DISASTER ID VALIDATION
            # -------------------------------------------------

            if not disaster_id.isdigit():

                flash(
                    "Disaster ID must be a valid number.",
                    "error"
                )

                return redirect(
                    url_for(
                        "requests.edit_request",
                        request_id=request_id
                    )
                )

            disaster_id = int(disaster_id)

            if disaster_id <= 0:

                flash(
                    "Disaster ID must be greater than 0.",
                    "error"
                )

                return redirect(
                    url_for(
                        "requests.edit_request",
                        request_id=request_id
                    )
                )

            # -------------------------------------------------
            # CHECK DISASTER EXISTS
            # -------------------------------------------------

            cursor.execute("""
                SELECT disaster_id
                FROM disasters
                WHERE disaster_id = %s
            """, (disaster_id,))

            disaster = cursor.fetchone()

            if not disaster:

                flash(
                    "Selected disaster does not exist.",
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
            # RESOURCE NAME VALIDATION
            # -------------------------------------------------

            if len(resource_name) < 2:

                flash(
                    "Resource name must contain at least 2 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "requests.edit_request",
                        request_id=request_id
                    )
                )

            if len(resource_name) > 150:

                flash(
                    "Resource name cannot exceed 150 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "requests.edit_request",
                        request_id=request_id
                    )
                )

            # -------------------------------------------------
            # QUANTITY VALIDATION
            # -------------------------------------------------

            if not quantity_requested.isdigit():

                flash(
                    "Quantity must be a valid positive number.",
                    "error"
                )

                return redirect(
                    url_for(
                        "requests.edit_request",
                        request_id=request_id
                    )
                )

            quantity_requested = int(quantity_requested)

            if quantity_requested <= 0:

                flash(
                    "Quantity must be greater than 0.",
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
                UPDATE resource_requests
                SET
                    disaster_id = %s,
                    resource_type = %s,
                    resource_name = %s,
                    quantity_requested = %s,
                    request_location = %s,
                    reason = %s,
                    priority = %s,
                    status = %s
                WHERE request_id = %s
            """, (
                disaster_id,
                request_type,
                resource_name,
                quantity_requested,
                location,
                description or None,
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
            FROM resource_requests
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
            DELETE FROM resource_requests
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