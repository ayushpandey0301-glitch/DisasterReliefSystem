from flask import Blueprint, render_template, session, redirect, url_for, flash
from utils.database import get_db_connection


reports = Blueprint("reports", __name__)


# =========================================================
# REPORTS & STATISTICS
# =========================================================

@reports.route("/reports")
def reports_home():

    # Check login
    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # ==========================================
        # TOTAL DISASTERS
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM disasters
        """)

        total_disasters = cursor.fetchone()["total"]


        # ==========================================
        # ACTIVE DISASTERS
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM disasters
            WHERE status = 'Active'
        """)

        active_disasters = cursor.fetchone()["total"]


        # ==========================================
        # TOTAL RESOURCES
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM resources
        """)

        total_resources = cursor.fetchone()["total"]


        # ==========================================
        # TOTAL SHELTERS
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM shelters
        """)

        total_shelters = cursor.fetchone()["total"]


        # ==========================================
        # TOTAL VEHICLES
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM vehicles
        """)

        total_vehicles = cursor.fetchone()["total"]


        # ==========================================
        # TOTAL VOLUNTEERS
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM users
            WHERE role = 'volunteer'
        """)

        total_volunteers = cursor.fetchone()["total"]


        # ==========================================
        # TOTAL RELIEF REQUESTS
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM resource_requests
        """)

        total_requests = cursor.fetchone()["total"]


        # ==========================================
        # RELIEF REQUESTS BY STATUS
        # ==========================================

        cursor.execute("""
            SELECT
                status,
                COUNT(*) AS total
            FROM resource_requests
            GROUP BY status
            ORDER BY total DESC
        """)

        requests_by_status = cursor.fetchall()


        # ==========================================
        # RELIEF REQUESTS BY PRIORITY
        # ==========================================

        cursor.execute("""
            SELECT
                priority,
                COUNT(*) AS total
            FROM resource_requests
            GROUP BY priority
            ORDER BY total DESC
        """)

        requests_by_priority = cursor.fetchall()


        # ==========================================
        # DISASTERS BY SEVERITY
        # ==========================================

        cursor.execute("""
            SELECT
                severity,
                COUNT(*) AS total
            FROM disasters
            GROUP BY severity
            ORDER BY total DESC
        """)

        disasters_by_severity = cursor.fetchall()


        # ==========================================
        # RESOURCES BY STATUS
        # ==========================================

        cursor.execute("""
            SELECT
                status,
                COUNT(*) AS total
            FROM resources
            GROUP BY status
            ORDER BY total DESC
        """)

        resources_by_status = cursor.fetchall()


        # ==========================================
        # VEHICLES BY STATUS
        # ==========================================

        cursor.execute("""
            SELECT
                status,
                COUNT(*) AS total
            FROM vehicles
            GROUP BY status
            ORDER BY total DESC
        """)

        vehicles_by_status = cursor.fetchall()


        # ==========================================
        # SHELTERS BY STATUS
        # ==========================================

        cursor.execute("""
            SELECT
                status,
                COUNT(*) AS total
            FROM shelters
            GROUP BY status
            ORDER BY total DESC
        """)

        shelters_by_status = cursor.fetchall()


        # ==========================================
        # VOLUNTEERS BY STATUS
        # ==========================================

        cursor.execute("""
            SELECT
                status,
                COUNT(*) AS total
            FROM users
            WHERE role = 'volunteer'
            GROUP BY status
            ORDER BY total DESC
        """)

        volunteers_by_status = cursor.fetchall()


        # ==========================================
        # REPORTS PAGE
        # ==========================================

        return render_template(
            "reports/reports.html",
            total_disasters=total_disasters,
            active_disasters=active_disasters,
            total_resources=total_resources,
            total_shelters=total_shelters,
            total_vehicles=total_vehicles,
            total_volunteers=total_volunteers,
            total_requests=total_requests,
            requests_by_status=requests_by_status,
            requests_by_priority=requests_by_priority,
            disasters_by_severity=disasters_by_severity,
            resources_by_status=resources_by_status,
            vehicles_by_status=vehicles_by_status,
            shelters_by_status=shelters_by_status,
            volunteers_by_status=volunteers_by_status
        )


    except Exception as e:

        print("REPORTS ERROR:", repr(e))

        flash(
            "Unable to load reports.",
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