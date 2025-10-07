from flask import request, jsonify
from database.db_handler import get_db_connection

def get_jobs_candidate_applied(candidateID):
    try:
        if not candidateID:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "CandidateID is required.",
                "isSuccess": False
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch jobs applied by the candidate
        cursor.execute("SELECT * FROM v_hm_candidate_job_mapping WHERE CandidateId = %s", (candidateID,))
        applied_jobs = cursor.fetchall()

        if not applied_jobs:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": f"No applied job details found for CandidateID {candidateID}.",
                "isSuccess": False,
                "result": None
            }), 404

        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": f"Applied jobs retrieved successfully for CandidateID {candidateID}.",
            "isSuccess": True,
            "result": applied_jobs
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
