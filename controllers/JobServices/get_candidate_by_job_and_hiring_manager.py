from flask import request, jsonify
from database.db_handler import get_db_connection

def get_candidate_by_job_and_hiring_manager(jobId, hiringManagerId):
    try:
        if not jobId or not hiringManagerId:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "Both JobId and HiringManagerId are required.",
                "isSuccess": False
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch candidates with upcoming interviews for the given JobId and HiringManagerId
        cursor.execute("""
            SELECT * 
            FROM v_hm_candidate_meeting 
            WHERE JobId = %s AND HiringManagerId = %s
        """, (jobId, hiringManagerId))
        candidates = cursor.fetchall()

        if not candidates:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": f"No upcoming interview data found for JobId {jobId} and HiringManagerId {hiringManagerId}.",
                "isSuccess": False,
                "result": None
            }), 404

        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": f"Upcoming interview data retrieved successfully for JobId {jobId} and HiringManagerId {hiringManagerId}.",
            "isSuccess": True,
            "result": candidates
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
