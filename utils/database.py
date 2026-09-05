import mysql.connector

from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    # =====================================================
    # LOCAL MYSQL
    # =====================================================

    if DB_HOST in ["localhost", "127.0.0.1"]:

        connection = mysql.connector.connect(
            host=DB_HOST,
            port=3306,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

    # =====================================================
    # REMOTE MYSQL - AIVEN / RENDER
    # =====================================================

    else:

        connection = mysql.connector.connect(
            host=DB_HOST,
            port=10732,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            ssl_verify_cert=False,
            ssl_verify_identity=False
        )

    # =====================================================
    # TEMPORARY RENDER DATABASE DIAGNOSTIC
    # =====================================================

    try:

        cursor = connection.cursor()

        cursor.execute("SELECT DATABASE()")
        current_database = cursor.fetchone()

        print("========================================")
        print("DATABASE DIAGNOSTIC")
        print("DB_HOST:", DB_HOST)
        print("DB_NAME FROM CONFIG:", DB_NAME)
        print("CURRENT DATABASE:", current_database)

        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        print("TABLES VISIBLE TO RENDER:")

        for table in tables:
            print(table)

        print("========================================")

        cursor.close()

    except Exception as diagnostic_error:

        print("DATABASE DIAGNOSTIC ERROR:", diagnostic_error)

    return connection