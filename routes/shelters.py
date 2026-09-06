from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.database import get_db_connection


shelters = Blueprint("shelters", __name__)


# =========================================================
# VALIDATION OPTIONS
# =========================================================

VALID_STATUSES = {
    "Available",
    "Full",
    "Closed"
}


# =========================================================
# ROLE PERMISSION HELPER
# =========================================================

def can_manage_shelters():

    user_role = session.get("role", "").lower()

    return user_role in ["admin", "coordinator"]


# =========================================================
# SHELTER LIST
# =========================================================

@shelters.route("/shelters")
def shelter_list():

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
                shelter_id,
                shelter_name,
                location,
                capacity,
                current_occupancy,
                contact_number,
                facilities,
                status,
                disaster_id,
                created_at
            FROM shelters
            ORDER BY created_at DESC
        """)

        shelter_records = cursor.fetchall()

        return render_template(
            "shelters/list.html",
            shelters=shelter_records
        )

    except Exception as e:

        print("SHELTER LIST ERROR:", repr(e))

        flash(
            "Unable to load shelter records.",
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
# ADD SHELTER
# =========================================================

@shelters.route("/shelters/add", methods=["GET", "POST"])
def add_shelter():

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    # ROLE PERMISSION
    if not can_manage_shelters():

        flash(
            "You do not have permission to add shelters.",
            "error"
        )

        return redirect(
            url_for("shelters.shelter_list")
        )

    if request.method == "POST":

        shelter_name = request.form.get(
            "shelter_name",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        capacity = request.form.get(
            "capacity",
            ""
        ).strip()

        current_occupancy = request.form.get(
            "current_occupancy",
            ""
        ).strip()

        contact_number = request.form.get(
            "contact_number",
            ""
        ).strip() or None

        facilities = request.form.get(
            "facilities",
            ""
        ).strip() or None

        status = request.form.get(
            "status",
            "Available"
        ).strip()

        disaster_id = request.form.get(
            "disaster_id",
            ""
        ).strip() or None


        # REQUIRED FIELD VALIDATION

        if not shelter_name or not location or not capacity:

            flash(
                "Shelter name, location and capacity are required.",
                "error"
            )

            return redirect(
                url_for("shelters.add_shelter")
            )


        # SHELTER NAME VALIDATION

        if len(shelter_name) < 2:

            flash(
                "Shelter name must contain at least 2 characters.",
                "error"
            )

            return redirect(
                url_for("shelters.add_shelter")
            )


        if len(shelter_name) > 150:

            flash(
                "Shelter name cannot exceed 150 characters.",
                "error"
            )

            return redirect(
                url_for("shelters.add_shelter")
            )


        # LOCATION VALIDATION

        if len(location) < 2:

            flash(
                "Location must contain at least 2 characters.",
                "error"
            )

            return redirect(
                url_for("shelters.add_shelter")
            )


        if len(location) > 255:

            flash(
                "Location cannot exceed 255 characters.",
                "error"
            )

            return redirect(
                url_for("shelters.add_shelter")
            )


        # CAPACITY VALIDATION

        try:

            capacity_value = int(capacity)

        except ValueError:

            flash(
                "Capacity must be a valid whole number.",
                "error"
            )

            return redirect(
                url_for("shelters.add_shelter")
            )


        if capacity_value <= 0:

            flash(
                "Capacity must be greater than 0.",
                "error"
            )

            return redirect(
                url_for("shelters.add_shelter")
            )


        # CURRENT OCCUPANCY VALIDATION

        if current_occupancy == "":
            occupancy_value = 0

        else:

            try:

                occupancy_value = int(current_occupancy)

            except ValueError:

                flash(
                    "Current occupancy must be a valid whole number.",
                    "error"
                )

                return redirect(
                    url_for("shelters.add_shelter")
                )


        if occupancy_value < 0:

            flash(
                "Current occupancy cannot be negative.",
                "error"
            )

            return redirect(
                url_for("shelters.add_shelter")
            )


        if occupancy_value > capacity_value:

            flash(
                "Current occupancy cannot exceed shelter capacity.",
                "error"
            )

            return redirect(
                url_for("shelters.add_shelter")
            )


        # CONTACT NUMBER VALIDATION

        if contact_number:

            if not contact_number.isdigit():

                flash(
                    "Contact number must contain only digits.",
                    "error"
                )

                return redirect(
                    url_for("shelters.add_shelter")
                )


            if len(contact_number) < 7 or len(contact_number) > 15:

                flash(
                    "Contact number must contain between 7 and 15 digits.",
                    "error"
                )

                return redirect(
                    url_for("shelters.add_shelter")
                )


        # FACILITIES VALIDATION

        if facilities and len(facilities) > 1000:

            flash(
                "Facilities description cannot exceed 1000 characters.",
                "error"
            )

            return redirect(
                url_for("shelters.add_shelter")
            )


        # STATUS VALIDATION

        if status not in VALID_STATUSES:

            flash(
                "Invalid shelter status selected.",
                "error"
            )

            return redirect(
                url_for("shelters.add_shelter")
            )


        # DISASTER ID VALIDATION

        disaster_id_value = None

        if disaster_id:

            try:

                disaster_id_value = int(disaster_id)

            except ValueError:

                flash(
                    "Invalid disaster selected.",
                    "error"
                )

                return redirect(
                    url_for("shelters.add_shelter")
                )


            if disaster_id_value <= 0:

                flash(
                    "Invalid disaster selected.",
                    "error"
                )

                return redirect(
                    url_for("shelters.add_shelter")
                )


            connection = None
            cursor = None

            try:

                connection = get_db_connection()
                cursor = connection.cursor()

                cursor.execute("""
                    SELECT disaster_id
                    FROM disasters
                    WHERE disaster_id = %s
                """, (disaster_id_value,))

                disaster_record = cursor.fetchone()

                if not disaster_record:

                    flash(
                        "Selected disaster does not exist.",
                        "error"
                    )

                    return redirect(
                        url_for("shelters.add_shelter")
                    )

            finally:

                if cursor:
                    cursor.close()

                if connection:
                    connection.close()


        # DATABASE INSERT

        connection = None
        cursor = None

        try:

            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO shelters
                (
                    shelter_name,
                    location,
                    capacity,
                    current_occupancy,
                    contact_number,
                    facilities,
                    status,
                    disaster_id
                )
                VALUES
                (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
            """, (
                shelter_name,
                location,
                capacity_value,
                occupancy_value,
                contact_number,
                facilities,
                status,
                disaster_id_value
            ))

            connection.commit()

            flash(
                "Shelter added successfully.",
                "success"
            )

            return redirect(
                url_for("shelters.shelter_list")
            )

        except Exception as e:

            if connection:
                connection.rollback()

            print(
                "ADD SHELTER ERROR:",
                repr(e)
            )

            flash(
                "Unable to add shelter.",
                "error"
            )

            return redirect(
                url_for("shelters.add_shelter")
            )

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template(
        "shelters/add.html"
    )


# =========================================================
# SHELTER DETAILS
# =========================================================

@shelters.route("/shelters/<int:shelter_id>")
def shelter_details(shelter_id):

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
                shelter_id,
                shelter_name,
                location,
                capacity,
                current_occupancy,
                contact_number,
                facilities,
                status,
                disaster_id,
                created_at
            FROM shelters
            WHERE shelter_id = %s
        """, (shelter_id,))

        shelter = cursor.fetchone()

        if not shelter:

            flash(
                "Shelter not found.",
                "error"
            )

            return redirect(
                url_for("shelters.shelter_list")
            )

        return render_template(
            "shelters/details.html",
            shelter=shelter
        )

    except Exception as e:

        print(
            "SHELTER DETAILS ERROR:",
            repr(e)
        )

        flash(
            "Unable to load shelter details.",
            "error"
        )

        return redirect(
            url_for("shelters.shelter_list")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# EDIT SHELTER
# =========================================================

@shelters.route(
    "/shelters/<int:shelter_id>/edit",
    methods=["GET", "POST"]
)
def edit_shelter(shelter_id):

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    # ROLE PERMISSION
    if not can_manage_shelters():

        flash(
            "You do not have permission to edit shelters.",
            "error"
        )

        return redirect(
            url_for("shelters.shelter_details", shelter_id=shelter_id)
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                shelter_id,
                shelter_name,
                location,
                capacity,
                current_occupancy,
                contact_number,
                facilities,
                status,
                disaster_id,
                created_at
            FROM shelters
            WHERE shelter_id = %s
        """, (shelter_id,))

        shelter = cursor.fetchone()

        if not shelter:

            flash(
                "Shelter not found.",
                "error"
            )

            return redirect(
                url_for("shelters.shelter_list")
            )


        if request.method == "POST":

            shelter_name = request.form.get(
                "shelter_name",
                ""
            ).strip()

            location = request.form.get(
                "location",
                ""
            ).strip()

            capacity = request.form.get(
                "capacity",
                ""
            ).strip()

            current_occupancy = request.form.get(
                "current_occupancy",
                ""
            ).strip()

            contact_number = request.form.get(
                "contact_number",
                ""
            ).strip() or None

            facilities = request.form.get(
                "facilities",
                ""
            ).strip() or None

            status = request.form.get(
                "status",
                "Available"
            ).strip()

            disaster_id = request.form.get(
                "disaster_id",
                ""
            ).strip() or None


            if not shelter_name or not location or not capacity:

                flash(
                    "Shelter name, location and capacity are required.",
                    "error"
                )

                return redirect(
                    url_for(
                        "shelters.edit_shelter",
                        shelter_id=shelter_id
                    )
                )


            if len(shelter_name) < 2 or len(shelter_name) > 150:

                flash(
                    "Shelter name must contain between 2 and 150 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "shelters.edit_shelter",
                        shelter_id=shelter_id
                    )
                )


            if len(location) < 2 or len(location) > 255:

                flash(
                    "Location must contain between 2 and 255 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "shelters.edit_shelter",
                        shelter_id=shelter_id
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
                        "shelters.edit_shelter",
                        shelter_id=shelter_id
                    )
                )


            if capacity_value <= 0:

                flash(
                    "Capacity must be greater than 0.",
                    "error"
                )

                return redirect(
                    url_for(
                        "shelters.edit_shelter",
                        shelter_id=shelter_id
                    )
                )


            if current_occupancy == "":
                occupancy_value = 0

            else:

                try:

                    occupancy_value = int(current_occupancy)

                except ValueError:

                    flash(
                        "Current occupancy must be a valid whole number.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "shelters.edit_shelter",
                            shelter_id=shelter_id
                        )
                    )


            if occupancy_value < 0 or occupancy_value > capacity_value:

                flash(
                    "Current occupancy must be between 0 and shelter capacity.",
                    "error"
                )

                return redirect(
                    url_for(
                        "shelters.edit_shelter",
                        shelter_id=shelter_id
                    )
                )


            if contact_number:

                if not contact_number.isdigit():

                    flash(
                        "Contact number must contain only digits.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "shelters.edit_shelter",
                            shelter_id=shelter_id
                        )
                    )


                if len(contact_number) < 7 or len(contact_number) > 15:

                    flash(
                        "Contact number must contain between 7 and 15 digits.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "shelters.edit_shelter",
                            shelter_id=shelter_id
                        )
                    )


            if facilities and len(facilities) > 1000:

                flash(
                    "Facilities description cannot exceed 1000 characters.",
                    "error"
                )

                return redirect(
                    url_for(
                        "shelters.edit_shelter",
                        shelter_id=shelter_id
                    )
                )


            if status not in VALID_STATUSES:

                flash(
                    "Invalid shelter status selected.",
                    "error"
                )

                return redirect(
                    url_for(
                        "shelters.edit_shelter",
                        shelter_id=shelter_id
                    )
                )


            disaster_id_value = None

            if disaster_id:

                try:

                    disaster_id_value = int(disaster_id)

                except ValueError:

                    flash(
                        "Invalid disaster selected.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "shelters.edit_shelter",
                            shelter_id=shelter_id
                        )
                    )


                if disaster_id_value <= 0:

                    flash(
                        "Invalid disaster selected.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "shelters.edit_shelter",
                            shelter_id=shelter_id
                        )
                    )


                cursor.execute("""
                    SELECT disaster_id
                    FROM disasters
                    WHERE disaster_id = %s
                """, (disaster_id_value,))

                disaster_record = cursor.fetchone()

                if not disaster_record:

                    flash(
                        "Selected disaster does not exist.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "shelters.edit_shelter",
                            shelter_id=shelter_id
                        )
                    )


            cursor.execute("""
                UPDATE shelters
                SET
                    shelter_name = %s,
                    location = %s,
                    capacity = %s,
                    current_occupancy = %s,
                    contact_number = %s,
                    facilities = %s,
                    status = %s,
                    disaster_id = %s
                WHERE shelter_id = %s
            """, (
                shelter_name,
                location,
                capacity_value,
                occupancy_value,
                contact_number,
                facilities,
                status,
                disaster_id_value,
                shelter_id
            ))

            connection.commit()

            flash(
                "Shelter updated successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "shelters.shelter_details",
                    shelter_id=shelter_id
                )
            )


        return render_template(
            "shelters/edit.html",
            shelter=shelter
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "EDIT SHELTER ERROR:",
            repr(e)
        )

        flash(
            "Unable to update shelter.",
            "error"
        )

        return redirect(
            url_for("shelters.shelter_list")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# DELETE SHELTER
# =========================================================

@shelters.route(
    "/shelters/<int:shelter_id>/delete",
    methods=["POST"]
)
def delete_shelter(shelter_id):

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    # ROLE PERMISSION
    if not can_manage_shelters():

        flash(
            "You do not have permission to delete shelters.",
            "error"
        )

        return redirect(
            url_for("shelters.shelter_list")
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT shelter_id
            FROM shelters
            WHERE shelter_id = %s
        """, (shelter_id,))

        shelter = cursor.fetchone()

        if not shelter:

            flash(
                "Shelter not found.",
                "error"
            )

            return redirect(
                url_for("shelters.shelter_list")
            )


        cursor.execute("""
            DELETE FROM shelters
            WHERE shelter_id = %s
        """, (shelter_id,))

        connection.commit()

        flash(
            "Shelter deleted successfully.",
            "success"
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "DELETE SHELTER ERROR:",
            repr(e)
        )

        flash(
            "Unable to delete shelter. It may be linked to other records.",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

    return redirect(
        url_for("shelters.shelter_list")
    )