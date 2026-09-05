from flask import Blueprint, render_template, session, redirect, url_for, flash
from utils.database import get_db_connection


dashboard = Blueprint("dashboard", __name__)


@dashboard.route("/dashboard")
def dashboard_home():

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
            WHERE status != 'Closed'
        """)

        total_shelters = cursor.fetchone()["total"]


        # ==========================================
        # TOTAL VOLUNTEERS
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM volunteers v
            JOIN users u
                ON v.user_id = u.user_id
            WHERE u.status = 'active'
        """)

        total_volunteers = cursor.fetchone()["total"]


        # ==========================================
        # RECENT DISASTERS
        # ==========================================

        cursor.execute("""
            SELECT
                disaster_id,
                disaster_name,
                disaster_type,
                location,
                severity,
                status,
                start_date
            FROM disasters
            ORDER BY created_at DESC
            LIMIT 5
        """)

        recent_disasters = cursor.fetchall()


        # ==========================================
        # RECENT RELIEF REQUESTS
        # ==========================================

        cursor.execute("""
            SELECT
                request_id,
                requester_name,
                request_type,
                location,
                priority,
                status,
                created_at
            FROM relief_requests
            ORDER BY created_at DESC
            LIMIT 5
        """)

        recent_requests = cursor.fetchall()


        # ==========================================
        # DASHBOARD
        # ==========================================

        return render_template(
            "dashboard/dashboard.html",
            active_disasters=active_disasters,
            total_resources=total_resources,
            total_shelters=total_shelters,
            total_volunteers=total_volunteers,
            recent_disasters=recent_disasters,
            recent_requests=recent_requests
        )


    except Exception as e:

        print("DASHBOARD ERROR:", repr(e))

        flash(
            "Unable to load dashboard data.",
            "error"
        )

        return render_template(
            "dashboard/dashboard.html",
            active_disasters=0,
            total_resources=0,
            total_shelters=0,
            total_volunteers=0,
            recent_disasters=[],
            recent_requests=[]
        )


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()
