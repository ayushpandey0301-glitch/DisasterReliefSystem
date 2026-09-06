from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.database import get_db_connection
from datetime import datetime


resource = Blueprint("resource", __name__)


# =========================================================
# VALIDATION OPTIONS
# =========================================================

VALID_RESOURCE_TYPES = {
    "Food",
    "Water",
    "Medicine",
    "Clothing",
    "Shelter Equipment",
    "Emergency Equipment",
    "Other"
}

VALID_STATUSES = {
    "Available",
    "Low Stock",
    "Out of Stock"
}


# =========================================================
# RESOURCE LIST
# =========================================================

@resource.route("/resources")
def resource_list():

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
                resource_id,
                resource_name,
                resource_type,
                quantity,
                unit,
                location,
                minimum_stock,
                expiry_date,
                status,
                created_at
            FROM resources
            ORDER BY created_at DESC
        """)

        resources = cursor.fetchall()

        return render_template(
            "resources/list.html",
            resources=resources
        )

    except Exception as e:

        print("RESOURCE LIST ERROR:", repr(e))

        flash(
            "Unable to load resource records.",
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
# RESOURCE DETAILS
# =========================================================

@resource.route("/resources/<int:resource_id>")
def resource_details(resource_id):

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
                resource_id,
                resource_name,
                resource_type,
                quantity,
                unit,
                location,
                minimum_stock,
                expiry_date,
                status,
                created_at
            FROM resources
            WHERE resource_id = %s
        """, (resource_id,))

        resource_record = cursor.fetchone()

        if not resource_record:

            flash(
                "Resource not found.",
                "error"
            )

            return redirect(
                url_for("resource.resource_list")
            )

        return render_template(
            "resources/details.html",
            resource=resource_record
        )

    except Exception as e:

        print(
            "RESOURCE DETAILS ERROR:",
            repr(e)
        )

        flash(
            "Unable to load resource details.",
            "error"
        )

        return redirect(
            url_for("resource.resource_list")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# ADD RESOURCE
# =========================================================

@resource.route("/resources/add", methods=["GET", "POST"])
def add_resource():

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        resource_name = request.form.get(
            "resource_name",
            ""
        ).strip()

        resource_type = request.form.get(
            "resource_type",
            ""
        ).strip()

        quantity = request.form.get(
            "quantity",
            ""
        ).strip()

        unit = request.form.get(
            "unit",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        minimum_stock = request.form.get(
            "minimum_stock",
            ""
        ).strip()

        expiry_date = request.form.get(
            "expiry_date",
            ""
        ).strip() or None

        status = request.form.get(
            "status",
            "Available"
        ).strip()


        # =================================================
        # REQUIRED FIELD VALIDATION
        # =================================================

        if (
            not resource_name
            or not resource_type
            or not quantity
            or not unit
            or not location
        ):

            flash(
                "Please fill in all required fields.",
                "error"
            )

            return redirect(
                url_for("resource.add_resource")
            )


        # =================================================
        # RESOURCE NAME VALIDATION
        # =================================================

        if len(resource_name) < 2:

            flash(
                "Resource name must contain at least 2 characters.",
                "error"
            )

            return redirect(
                url_for("resource.add_resource")
            )

        if len(resource_name) > 150:

            flash(
                "Resource name cannot exceed 150 characters.",
                "error"
            )

            return redirect(
                url_for("resource.add_resource")
            )


        # =================================================
        # UNIT VALIDATION
        # =================================================

        if len(unit) > 50:

            flash(
                "Unit cannot exceed 50 characters.",
                "error"
            )

            return redirect(
                url_for("resource.add_resource")
            )


        # =================================================
        # LOCATION VALIDATION
        # =================================================

        if len(location) < 2:

            flash(
                "Location must contain at least 2 characters.",
                "error"
            )

            return redirect(
                url_for("resource.add_resource")
            )

        if len(location) > 255:

            flash(
                "Location cannot exceed 255 characters.",
                "error"
            )

            return redirect(
                url_for("resource.add_resource")
            )


        # =================================================
        # RESOURCE TYPE VALIDATION
        # =================================================

        if resource_type not in VALID_RESOURCE_TYPES:

            flash(
                "Invalid resource type selected.",
                "error"
            )

            return redirect(
                url_for("resource.add_resource")
            )


        # =================================================
        # QUANTITY VALIDATION
        # =================================================

        try:

            quantity_value = int(quantity)

        except ValueError:

            flash(
                "Quantity must be a valid whole number.",
                "error"
            )

            return redirect(
                url_for("resource.add_resource")
            )

        if quantity_value < 0:

            flash(
                "Quantity cannot be negative.",
                "error"
            )

            return redirect(
                url_for("resource.add_resource")
            )


        # =================================================
        # MINIMUM STOCK VALIDATION
        # =================================================

        if minimum_stock == "":

            minimum_stock_value = 0

        else:

            try:

                minimum_stock_value = int(minimum_stock)

            except ValueError:

                flash(
                    "Minimum stock must be a valid whole number.",
                    "error"
                )

                return redirect(
                    url_for("resource.add_resource")
                )

        if minimum_stock_value < 0:

            flash(
                "Minimum stock cannot be negative.",
                "error"
            )

            return redirect(
                url_for("resource.add_resource")
            )


        # =================================================
        # STATUS VALIDATION
        # =================================================

        if status not in VALID_STATUSES:

            flash(
                "Invalid resource status selected.",
                "error"
            )

            return redirect(
                url_for("resource.add_resource")
            )


        # =================================================
        # EXPIRY DATE VALIDATION
        # =================================================

        if expiry_date:

            try:

                datetime.strptime(
                    expiry_date,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "Invalid expiry date.",
                    "error"
                )

                return redirect(
                    url_for("resource.add_resource")
                )


        # =================================================
        # DATABASE INSERT
        # =================================================

        connection = None
        cursor = None

        try:

            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO resources
                (
                    resource_name,
                    resource_type,
                    quantity,
                    unit,
                    location,
                    minimum_stock,
                    expiry_date,
                    status
                )
                VALUES
                (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
            """, (
                resource_name,
                resource_type,
                quantity_value,
                unit,
                location,
                minimum_stock_value,
                expiry_date,
                status
            ))

            connection.commit()

            flash(
                "Resource added successfully.",
                "success"
            )

            return redirect(
                url_for("resource.resource_list")
            )

        except Exception as e:

            if connection:
                connection.rollback()

            print(
                "ADD RESOURCE ERROR:",
                repr(e)
            )

            flash(
                "Unable to add resource.",
                "error"
            )

            return redirect(
                url_for("resource.add_resource")
            )

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template(
        "resources/add.html"
    )


# =========================================================
# EDIT RESOURCE
# =========================================================

@resource.route(
    "/resources/<int:resource_id>/edit",
    methods=["GET", "POST"]
)
def edit_resource(resource_id):

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # -------------------------------------------------
        # GET EXISTING RESOURCE
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                resource_id,
                resource_name,
                resource_type,
                quantity,
                unit,
                location,
                minimum_stock,
                expiry_date,
                status,
                created_at
            FROM resources
            WHERE resource_id = %s
        """, (resource_id,))

        resource_record = cursor.fetchone()

        if not resource_record:

            flash(
                "Resource not found.",
                "error"
            )

            return redirect(
                url_for("resource.resource_list")
            )


        # -------------------------------------------------
        # UPDATE RESOURCE
        # -------------------------------------------------

        if request.method == "POST":

            resource_name = request.form.get(
                "resource_name",
                ""
            ).strip()

            resource_type = request.form.get(
                "resource_type",
                ""
            ).strip()

            quantity = request.form.get(
                "quantity",
                ""
            ).strip()

            unit = request.form.get(
                "unit",
                ""
            ).strip()

            location = request.form.get(
                "location",
                ""
            ).strip()

            minimum_stock = request.form.get(
                "minimum_stock",
                ""
            ).strip()

            expiry_date = request.form.get(
                "expiry_date",
                ""
            ).strip() or None

            status = request.form.get(
                "status",
                "Available"
            ).strip()


            # =============================================
            # REQUIRED FIELD VALIDATION
            # =============================================

            if (
                not resource_name
                or not resource_type
                or not quantity
                or not unit
                or not location
            ):

                flash(
                    "Please fill in all required fields.",
                    "error"
                )

                return redirect(
                    url_for(
                        "resource.edit_resource",
                        resource_id=resource_id
                    )
                )


            # =============================================
            # RESOURCE NAME VALIDATION
            # =============================================

            if len(resource_name) < 2:

                flash(
                    "Resource name must contain at least 2 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "resource.edit_resource",
                        resource_id=resource_id
                    )
                )

            if len(resource_name) > 150:

                flash(
                    "Resource name cannot exceed 150 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "resource.edit_resource",
                        resource_id=resource_id
                    )
                )


            # =============================================
            # RESOURCE TYPE VALIDATION
            # =============================================

            if resource_type not in VALID_RESOURCE_TYPES:

                flash(
                    "Invalid resource type selected.",
                    "error"
                )

                return redirect(
                    url_for(
                        "resource.edit_resource",
                        resource_id=resource_id
                    )
                )


            # =============================================
            # QUANTITY VALIDATION
            # =============================================

            try:

                quantity_value = int(quantity)

            except ValueError:

                flash(
                    "Quantity must be a valid whole number.",
                    "error"
                )

                return redirect(
                    url_for(
                        "resource.edit_resource",
                        resource_id=resource_id
                    )
                )

            if quantity_value < 0:

                flash(
                    "Quantity cannot be negative.",
                    "error"
                )

                return redirect(
                    url_for(
                        "resource.edit_resource",
                        resource_id=resource_id
                    )
                )


            # =============================================
            # MINIMUM STOCK VALIDATION
            # =============================================

            if minimum_stock == "":

                minimum_stock_value = 0

            else:

                try:

                    minimum_stock_value = int(
                        minimum_stock
                    )

                except ValueError:

                    flash(
                        "Minimum stock must be a valid whole number.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "resource.edit_resource",
                            resource_id=resource_id
                        )
                    )

            if minimum_stock_value < 0:

                flash(
                    "Minimum stock cannot be negative.",
                    "error"
                )

                return redirect(
                    url_for(
                        "resource.edit_resource",
                        resource_id=resource_id
                    )
                )


            # =============================================
            # STATUS VALIDATION
            # =============================================

            if status not in VALID_STATUSES:

                flash(
                    "Invalid resource status selected.",
                    "error"
                )

                return redirect(
                    url_for(
                        "resource.edit_resource",
                        resource_id=resource_id
                    )
                )


            # =============================================
            # EXPIRY DATE VALIDATION
            # =============================================

            if expiry_date:

                try:

                    datetime.strptime(
                        expiry_date,
                        "%Y-%m-%d"
                    ).date()

                except ValueError:

                    flash(
                        "Invalid expiry date.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "resource.edit_resource",
                            resource_id=resource_id
                        )
                    )


            # =============================================
            # DATABASE UPDATE
            # =============================================

            cursor.execute("""
                UPDATE resources
                SET
                    resource_name = %s,
                    resource_type = %s,
                    quantity = %s,
                    unit = %s,
                    location = %s,
                    minimum_stock = %s,
                    expiry_date = %s,
                    status = %s
                WHERE resource_id = %s
            """, (
                resource_name,
                resource_type,
                quantity_value,
                unit,
                location,
                minimum_stock_value,
                expiry_date,
                status,
                resource_id
            ))

            connection.commit()

            flash(
                "Resource updated successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "resource.resource_details",
                    resource_id=resource_id
                )
            )


        return render_template(
            "resources/edit.html",
            resource=resource_record
        )


    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "EDIT RESOURCE ERROR:",
            repr(e)
        )

        flash(
            "Unable to update resource.",
            "error"
        )

        return redirect(
            url_for(
                "resource.resource_list"
            )
        )


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# DELETE RESOURCE - ADMIN ONLY
# =========================================================

@resource.route(
    "/resources/delete/<int:resource_id>",
    methods=["POST"]
)
def delete_resource(resource_id):

    # -------------------------------------------------
    # LOGIN CHECK
    # -------------------------------------------------

    if "user_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )


    # -------------------------------------------------
    # ADMIN CHECK
    # -------------------------------------------------

    if session.get("role") != "admin":

        flash(
            "Only administrators are allowed to delete resources.",
            "error"
        )

        return redirect(
            url_for("resource.resource_list")
        )


    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()


        # -------------------------------------------------
        # CHECK RESOURCE EXISTS
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT resource_id
            FROM resources
            WHERE resource_id = %s
            """,
            (resource_id,)
        )

        resource_record = cursor.fetchone()


        if not resource_record:

            flash(
                "Resource not found.",
                "error"
            )

            return redirect(
                url_for("resource.resource_list")
            )


        # -------------------------------------------------
        # DELETE RESOURCE
        # -------------------------------------------------

        cursor.execute(
            """
            DELETE FROM resources
            WHERE resource_id = %s
            """,
            (resource_id,)
        )

        connection.commit()


        flash(
            "Resource deleted successfully.",
            "success"
        )


    except Exception as e:

        if connection:

            connection.rollback()


        print(
            "DELETE RESOURCE ERROR:",
            repr(e)
        )


        flash(
            "Unable to delete resource.",
            "error"
        )


    finally:

        if cursor:

            cursor.close()

        if connection:

            connection.close()


    return redirect(
        url_for("resource.resource_list")
    )