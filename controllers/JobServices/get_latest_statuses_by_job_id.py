from flask import request, jsonify
from database.db_handler import get_db_connection

def get_latest_statuses_by_job_id(jobId):
    try:
        if not jobId:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "JobId is required.",
                "isSuccess": False
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch latest statuses for the given JobId
        cursor.execute("SELECT * FROM v_hm_candidate_shortlisted WHERE JobId = %s", (jobId,))
        statuses = cursor.fetchall()

        if not statuses:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": f"No statuses found for JobId {jobId}.",
                "isSuccess": False,
                "result": None
            }), 404

        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": f"Statuses retrieved successfully for JobId {jobId}.",
            "isSuccess": True,
            "result": statuses
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
