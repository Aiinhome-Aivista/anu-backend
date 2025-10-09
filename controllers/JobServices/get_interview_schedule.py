from flask import request, jsonify
from database.db_handler import get_db_connection


def get_interview_schedule():
    try:
        data = request.get_json()
        if not data or "jobId" not in data or "CandidateId" not in data:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "Invalid input data. 'jobId' and 'CandidateId' are required.",
                "isSuccess": False
            }), 400

        jobId = data["jobId"]
        candidateId = data["CandidateId"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * 
            FROM v_hm_candidate_meeting 
            WHERE JobId = %s AND CandidateId = %s
        """, (jobId, candidateId))
        schedule = cursor.fetchall()

        if not schedule:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": f"No interview schedule found for JobId {jobId} and CandidateId {candidateId}.",
                "isSuccess": False,
                "result": None
            }), 404

        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": f"Interview schedule retrieved successfully for JobId {jobId} and CandidateId {candidateId}.",
            "isSuccess": True,
            "result": schedule
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