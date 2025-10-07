from flask import request,jsonify
from database.db_handler import get_db_connection

def call_update_profile_journey_status():
    try:
        data = request.get_json()

        # Validate input
        if not data or "JobId" not in data or "CandidateId" not in data or "ProfileJourney" not in data or "Status" not in data:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "Invalid input data. Required fields: JobId, CandidateId, ProfileJourney, Status, and optional Score.",
                "isSuccess": False
            }), 400

        job_id = data["JobId"]
        candidate_id = data["CandidateId"]
        profile_journey = data["ProfileJourney"]
        status = data["Status"]
        score = data.get("Score", None)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Call the stored procedure (similar to C#)
        cursor.callproc("UpdateProfileJourneyStatus", [
            job_id,
            candidate_id,
            profile_journey,
            status,
            score
        ])
        conn.commit()

        # Success response
        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": "Stored procedure executed successfully.",
            "isSuccess": True,
            "result": {
                "JobId": job_id,
                "CandidateId": candidate_id,
                "ProfileJourney": profile_journey,
                "Status": status,
                "Score": score
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "failed",
            "statusCode": 500,
            "message": f"An error occurred: {str(e)}",
            "isSuccess": False
        }), 500

    finally:
        try:
            if conn.is_connected():
                cursor.close()
                conn.close()
        except:
            pass

