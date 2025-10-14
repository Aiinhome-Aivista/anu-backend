from datetime import timedelta
from flask import request, jsonify
from database.db_handler import get_db_connection

def get_candidate_by_job_and_hiring_manager(jobId, hiringManagerId):
    try:
        # Validate required parameters
        if not jobId or not hiringManagerId:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "Both JobId and HiringManagerId are required.",
                "isSuccess": False
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Enhanced query with INNER JOINs
        cursor.execute("""
            SELECT 
                a.*, 
                b.first_name, 
                b.last_name, 
                c.role
            FROM 
                hiringmanagerselectedslots AS a
            INNER JOIN 
                candidateprofile AS b ON a.candidateId = b.id
            INNER JOIN 
                job AS c ON a.jobid = c.id
            WHERE 
                a.jobid = %s AND a.hiringManagerId = %s
        """, (jobId, hiringManagerId))

        candidates = cursor.fetchall()

        # Convert timedelta fields for JSON serialization
        for candidate in candidates:
            for key, value in candidate.items():
                if isinstance(value, timedelta):
                    candidate[key] = str(value)

        # If no results found
        if not candidates:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": f"No upcoming interview data found for JobId {jobId} and HiringManagerId {hiringManagerId}.",
                "isSuccess": False,
                "result": None
            }), 404

        # Success response
        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": f"Upcoming interview data retrieved successfully for JobId {jobId} and HiringManagerId {hiringManagerId}.",
            "isSuccess": True,
            "result": candidates
        }), 200

    except Exception as e:
        # Error handler
        return jsonify({
            "status": "failed",
            "statusCode": 500,
            "message": str(e),
            "isSuccess": False
        }), 500

    finally:
        # Close DB connection
        try:
            if conn.is_connected():
                cursor.close()
                conn.close()
        except:
            pass