from flask import request, jsonify
from database.db_handler import get_db_connection

def applied_job_by_candidate():
    try:
        # Get JSON body
        data = request.get_json()
        if not data or "job_id" not in data:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "job_id is required in request body.",
                "isSuccess": False
            }), 400

        job_id = data["job_id"]

        # Get DB connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Call the stored procedure
        cursor.callproc("update_job_init_status", [job_id])
        conn.commit()

        # Optional: you can also fetch rowcount or affected rows if needed
        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": f"Job initialization status updated successfully for JobId: {job_id}.",
            "isSuccess": True
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
