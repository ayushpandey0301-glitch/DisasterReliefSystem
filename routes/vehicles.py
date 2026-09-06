from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.database import get_db_connection


vehicles = Blueprint("vehicles", __name__)


# =========================================================
# VALIDATION OPTIONS
# =========================================================

VALID_VEHICLE_TYPES = {
    "Ambulance",
    "Truck",
    "Van",
    "Rescue Vehicle",
    "Other"
}

VALID_STATUSES = {
    "Available",
    "In Use",
    "Maintenance"
}


# =========================================================
# ROLE PERMISSION
# =========================================================

def can_manage_vehicles():

    return (
        "user_id" in session
        and session.get("role") in ["admin", "coordinator"]
    )


# =========================================
# VEHICLE LIST
# =========================================

@vehicles.route("/vehicles")
def vehicle_list():

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM vehicles
            ORDER BY vehicle_id DESC
        """)

        vehicles_data = cursor.fetchall()

        return render_template(
            "vehicles/list.html",
            vehicles=vehicles_data
        )

    except Exception as e:

        print("VEHICLE LIST ERROR:", repr(e))

        flash(
            "Unable to load vehicles.",
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


# =========================================
# ADD VEHICLE
# =========================================

@vehicles.route(
    "/vehicles/add",
    methods=["GET", "POST"]
)
def add_vehicle():

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        vehicle_number = request.form.get(
            "vehicle_number",
            ""
        ).strip()

        vehicle_type = request.form.get(
            "vehicle_type",
            ""
        ).strip()

        capacity = request.form.get(
            "capacity",
            ""
        ).strip()

        driver_name = request.form.get(
            "driver_name",
            ""
        ).strip()

        driver_contact = request.form.get(
            "driver_contact",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        status = request.form.get(
            "status",
            ""
        ).strip()


        # =========================================
        # REQUIRED FIELD VALIDATION
        # =========================================

        if (
            not vehicle_number
            or not vehicle_type
            or not capacity
            or not location
            or not status
        ):

            flash(
                "Vehicle number, vehicle type, capacity, location and status are required.",
                "error"
            )

            return redirect(
                url_for("vehicles.add_vehicle")
            )


        # =========================================
        # VEHICLE NUMBER VALIDATION
        # =========================================

        if len(vehicle_number) < 2:

            flash(
                "Vehicle number must contain at least 2 characters.",
                "error"
            )

            return redirect(
                url_for("vehicles.add_vehicle")
            )


        if len(vehicle_number) > 50:

            flash(
                "Vehicle number cannot exceed 50 characters.",
                "error"
            )

            return redirect(
                url_for("vehicles.add_vehicle")
            )


        # =========================================
        # VEHICLE TYPE VALIDATION
        # =========================================

        if vehicle_type not in VALID_VEHICLE_TYPES:

            flash(
                "Invalid vehicle type selected.",
                "error"
            )

            return redirect(
                url_for("vehicles.add_vehicle")
            )


        # =========================================
        # CAPACITY VALIDATION
        # =========================================

        try:

            capacity_value = int(capacity)

        except ValueError:

            flash(
                "Capacity must be a valid whole number.",
                "error"
            )

            return redirect(
                url_for("vehicles.add_vehicle")
            )


        if capacity_value <= 0:

            flash(
                "Capacity must be greater than 0.",
                "error"
            )

            return redirect(
                url_for("vehicles.add_vehicle")
            )


        # =========================================
        # DRIVER NAME VALIDATION
        # =========================================

        if driver_name:

            if len(driver_name) < 2:

                flash(
                    "Driver name must contain at least 2 characters.",
                    "error"
                )

                return redirect(
                    url_for("vehicles.add_vehicle")
                )


            if len(driver_name) > 100:

                flash(
                    "Driver name cannot exceed 100 characters.",
                    "error"
                )

                return redirect(
                    url_for("vehicles.add_vehicle")
                )


        # =========================================
        # DRIVER CONTACT VALIDATION
        # =========================================

        if driver_contact:

            if not driver_contact.isdigit():

                flash(
                    "Driver contact must contain only digits.",
                    "error"
                )

                return redirect(
                    url_for("vehicles.add_vehicle")
                )


            if len(driver_contact) < 7 or len(driver_contact) > 15:

                flash(
                    "Driver contact must contain between 7 and 15 digits.",
                    "error"
                )

                return redirect(
                    url_for("vehicles.add_vehicle")
                )


        # =========================================
        # LOCATION VALIDATION
        # =========================================

        if len(location) < 2:

            flash(
                "Location must contain at least 2 characters.",
                "error"
            )

            return redirect(
                url_for("vehicles.add_vehicle")
            )


        if len(location) > 255:

            flash(
                "Location cannot exceed 255 characters.",
                "error"
            )

            return redirect(
                url_for("vehicles.add_vehicle")
            )


        # =========================================
        # STATUS VALIDATION
        # =========================================

        if status not in VALID_STATUSES:

            flash(
                "Invalid vehicle status selected.",
                "error"
            )

            return redirect(
                url_for("vehicles.add_vehicle")
            )


        connection = None
        cursor = None

        try:

            connection = get_db_connection()

            cursor = connection.cursor()


            # =========================================
            # CHECK DUPLICATE VEHICLE NUMBER
            # =========================================

            cursor.execute("""
                SELECT vehicle_id
                FROM vehicles
                WHERE vehicle_number = %s
            """, (vehicle_number,))

            existing_vehicle = cursor.fetchone()

            if existing_vehicle:

                flash(
                    "A vehicle with this vehicle number already exists.",
                    "error"
                )

                return redirect(
                    url_for("vehicles.add_vehicle")
                )


            # =========================================
            # INSERT VEHICLE
            # =========================================

            cursor.execute("""
                INSERT INTO vehicles
                (
                    vehicle_number,
                    vehicle_type,
                    capacity,
                    driver_name,
                    driver_contact,
                    location,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                vehicle_number,
                vehicle_type,
                capacity_value,
                driver_name or None,
                driver_contact or None,
                location,
                status
            ))

            connection.commit()

            flash(
                "Vehicle added successfully.",
                "success"
            )

            return redirect(
                url_for("vehicles.vehicle_list")
            )

        except Exception as e:

            if connection:
                connection.rollback()

            print(
                "ADD VEHICLE ERROR:",
                repr(e)
            )

            flash(
                "Unable to add vehicle.",
                "error"
            )

            return redirect(
                url_for("vehicles.add_vehicle")
            )

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template(
        "vehicles/add.html"
    )


# =========================================
# VEHICLE DETAILS
# =========================================

@vehicles.route("/vehicles/<int:vehicle_id>")
def vehicle_details(vehicle_id):

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM vehicles
            WHERE vehicle_id = %s
        """, (vehicle_id,))

        vehicle = cursor.fetchone()

        if not vehicle:

            flash(
                "Vehicle not found.",
                "error"
            )

            return redirect(
                url_for("vehicles.vehicle_list")
            )

        return render_template(
            "vehicles/details.html",
            vehicle=vehicle
        )

    except Exception as e:

        print(
            "VEHICLE DETAILS ERROR:",
            repr(e)
        )

        flash(
            "Unable to load vehicle details.",
            "error"
        )

        return redirect(
            url_for("vehicles.vehicle_list")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================
# EDIT VEHICLE
# =========================================

@vehicles.route(
    "/vehicles/<int:vehicle_id>/edit",
    methods=["GET", "POST"]
)
def edit_vehicle(vehicle_id):

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)


        # =========================================
        # GET EXISTING VEHICLE
        # =========================================

        cursor.execute("""
            SELECT *
            FROM vehicles
            WHERE vehicle_id = %s
        """, (vehicle_id,))

        vehicle = cursor.fetchone()

        if not vehicle:

            flash(
                "Vehicle not found.",
                "error"
            )

            return redirect(
                url_for("vehicles.vehicle_list")
            )


        # =========================================
        # UPDATE VEHICLE
        # =========================================

        if request.method == "POST":

            vehicle_number = request.form.get(
                "vehicle_number",
                ""
            ).strip()

            vehicle_type = request.form.get(
                "vehicle_type",
                ""
            ).strip()

            capacity = request.form.get(
                "capacity",
                ""
            ).strip()

            driver_name = request.form.get(
                "driver_name",
                ""
            ).strip()

            driver_contact = request.form.get(
                "driver_contact",
                ""
            ).strip()

            location = request.form.get(
                "location",
                ""
            ).strip()

            status = request.form.get(
                "status",
                ""
            ).strip()


            if (
                not vehicle_number
                or not vehicle_type
                or not capacity
                or not location
                or not status
            ):

                flash(
                    "Vehicle number, vehicle type, capacity, location and status are required.",
                    "error"
                )

                return redirect(
                    url_for(
                        "vehicles.edit_vehicle",
                        vehicle_id=vehicle_id
                    )
                )


            if len(vehicle_number) < 2 or len(vehicle_number) > 50:

                flash(
                    "Vehicle number must contain between 2 and 50 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "vehicles.edit_vehicle",
                        vehicle_id=vehicle_id
                    )
                )


            if vehicle_type not in VALID_VEHICLE_TYPES:

                flash(
                    "Invalid vehicle type selected.",
                    "error"
                )

                return redirect(
                    url_for(
                        "vehicles.edit_vehicle",
                        vehicle_id=vehicle_id
                    )
                )


            try:

                capacity_value = int(capacity)

            except ValueError:

                flash(
                    "Capacity must be a valid whole number.",
                    "error"
                )

                return redirect(
                    url_for(
                        "vehicles.edit_vehicle",
                        vehicle_id=vehicle_id
                    )
                )


            if capacity_value <= 0:

                flash(
                    "Capacity must be greater than 0.",
                    "error"
                )

                return redirect(
                    url_for(
                        "vehicles.edit_vehicle",
                        vehicle_id=vehicle_id
                    )
                )


            if driver_name:

                if len(driver_name) < 2 or len(driver_name) > 100:

                    flash(
                        "Driver name must contain between 2 and 100 characters.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "vehicles.edit_vehicle",
                            vehicle_id=vehicle_id
                        )
                    )


            if driver_contact:

                if not driver_contact.isdigit():

                    flash(
                        "Driver contact must contain only digits.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "vehicles.edit_vehicle",
                            vehicle_id=vehicle_id
                        )
                    )


                if len(driver_contact) < 7 or len(driver_contact) > 15:

                    flash(
                        "Driver contact must contain between 7 and 15 digits.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "vehicles.edit_vehicle",
                            vehicle_id=vehicle_id
                        )
                    )


            if len(location) < 2 or len(location) > 255:

                flash(
                    "Location must contain between 2 and 255 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "vehicles.edit_vehicle",
                        vehicle_id=vehicle_id
                    )
                )


            if status not in VALID_STATUSES:

                flash(
                    "Invalid vehicle status selected.",
                    "error"
                )

                return redirect(
                    url_for(
                        "vehicles.edit_vehicle",
                        vehicle_id=vehicle_id
                    )
                )


            # =========================================
            # CHECK DUPLICATE VEHICLE NUMBER
            # =========================================

            cursor.execute("""
                SELECT vehicle_id
                FROM vehicles
                WHERE vehicle_number = %s
                AND vehicle_id != %s
            """, (
                vehicle_number,
                vehicle_id
            ))

            existing_vehicle = cursor.fetchone()

            if existing_vehicle:

                flash(
                    "A vehicle with this vehicle number already exists.",
                    "error"
                )

                return redirect(
                    url_for(
                        "vehicles.edit_vehicle",
                        vehicle_id=vehicle_id
                    )
                )


            # =========================================
            # DATABASE UPDATE
            # =========================================

            cursor.execute("""
                UPDATE vehicles
                SET
                    vehicle_number = %s,
                    vehicle_type = %s,
                    capacity = %s,
                    driver_name = %s,
                    driver_contact = %s,
                    location = %s,
                    status = %s
                WHERE vehicle_id = %s
            """, (
                vehicle_number,
                vehicle_type,
                capacity_value,
                driver_name or None,
                driver_contact or None,
                location,
                status,
                vehicle_id
            ))

            connection.commit()

            flash(
                "Vehicle updated successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "vehicles.vehicle_details",
                    vehicle_id=vehicle_id
                )
            )


        return render_template(
            "vehicles/edit.html",
            vehicle=vehicle
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "EDIT VEHICLE ERROR:",
            repr(e)
        )

        flash(
            "Unable to update vehicle.",
            "error"
        )

        return redirect(
            url_for(
                "vehicles.vehicle_details",
                vehicle_id=vehicle_id
            )
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================
# DELETE VEHICLE
# ADMIN / COORDINATOR ONLY
# =========================================

@vehicles.route(
    "/vehicles/<int:vehicle_id>/delete",
    methods=["POST"]
)
def delete_vehicle(vehicle_id):

    if "user_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )


    # =========================================
    # ROLE SECURITY
    # =========================================

    if not can_manage_vehicles():

        flash(
            "You do not have permission to delete vehicles.",
            "error"
        )

        return redirect(
            url_for(
                "vehicles.vehicle_details",
                vehicle_id=vehicle_id
            )
        )


    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()


        # =========================================
        # CHECK VEHICLE EXISTS
        # =========================================

        cursor.execute("""
            SELECT vehicle_id
            FROM vehicles
            WHERE vehicle_id = %s
        """, (vehicle_id,))

        vehicle = cursor.fetchone()

        if not vehicle:

            flash(
                "Vehicle not found.",
                "error"
            )

            return redirect(
                url_for("vehicles.vehicle_list")
            )


        # =========================================
        # DELETE VEHICLE
        # =========================================

        cursor.execute("""
            DELETE FROM vehicles
            WHERE vehicle_id = %s
        """, (vehicle_id,))

        connection.commit()

        flash(
            "Vehicle deleted successfully.",
            "success"
        )

        return redirect(
            url_for("vehicles.vehicle_list")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "DELETE VEHICLE ERROR:",
            repr(e)
        )

        flash(
            "Unable to delete vehicle.",
            "error"
        )

        return redirect(
            url_for(
                "vehicles.vehicle_details",
                vehicle_id=vehicle_id
            )
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()