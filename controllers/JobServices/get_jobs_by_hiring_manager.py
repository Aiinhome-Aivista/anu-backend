from flask import request, jsonify
from database.db_handler import get_db_connection

def get_jobs_by_hiring_manager(hiringManagerId):
    try:
        if not hiringManagerId:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "HiringManagerId is required.",
                "isSuccess": False
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM job WHERE HiringManagerId = %s", (hiringManagerId,))
        jobs = cursor.fetchall()

        if not jobs:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": f"No jobs found for HiringManagerId {hiringManagerId}.",
                "isSuccess": False,
                "result": None
            }), 404

        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": f"Jobs retrieved successfully for HiringManagerId {hiringManagerId}.",
            "isSuccess": True,
            "result": jobs
        }), 200

    except Exception as e:
        return jsonify({
            "status": "failed",
            "statusCode": 500,
            "message": str(e),
            "isSuccess": False
        }), 500

    finally:
        try:
            if conn.is_connected():
                cursor.close()
                conn.close()
        except:
            pass
