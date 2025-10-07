from flask import request, jsonify
from database.db_handler import get_db_connection

def get_details_candidate_applied(jobId):
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

        # Fetch candidate application details for the given JobId
        cursor.execute("SELECT * FROM v_hm_candidate_applied WHERE JobId = %s", (jobId,))
        details = cursor.fetchall()

        if not details:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": f"No candidate details found for JobId {jobId}.",
                "isSuccess": False,
                "result": None
            }), 404

        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": f"Candidate details retrieved successfully for JobId {jobId}.",
            "isSuccess": True,
            "result": details
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
