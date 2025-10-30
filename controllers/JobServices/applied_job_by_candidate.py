from flask import request, jsonify
from database.db_handler import get_db_connection

def applied_job_by_candidate():
    try:
        # Parse request body
        data = request.get_json()
        if not data or "job_id" not in data or "candidate_id" not in data:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "job_id and candidate_id are required in request body.",
                "isSuccess": False
            }), 400

        job_id = data["job_id"]
        candidate_id = data["candidate_id"]

        # Connect to DB
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch candidate score
        cursor.execute("""
            SELECT jobmatchscore
            FROM jobapplication
            WHERE JobId = %s AND CandidateId = %s
        """, (job_id, candidate_id))
        result = cursor.fetchone()

        if not result:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": "No matching job application found.",
                "isSuccess": False
            }), 404

        
         # Convert safely to number
        try:
            match_score = float(result.get("jobmatchscore", 0))
        except (TypeError, ValueError):
            match_score = 0  

        # If score < 30 → Not Shortlisted
        if match_score < 20:
            cursor.execute("""
                UPDATE jobapplication
                SET LatestStatus = 'Not ShortListed'
                WHERE JobId = %s AND CandidateId = %s AND LatestStatus = 'Inactive'
            """, (job_id, candidate_id))

            cursor.execute("""
                INSERT INTO jobassessments (JobId, CandidateId, assessmentSqnc, AssessmentName, Status)
                VALUES (%s, %s, 1, 'Not Appear', 'Not Shortlisted')
            """, (job_id, candidate_id))

            conn.commit()

            message = f"Candidate {candidate_id} not shortlisted for Job {job_id} (job match score : {match_score})."

        else:
            # Call stored procedure (normal flow)
            cursor.callproc("update_job_init_status", [job_id, candidate_id])
            conn.commit()
            message = f"Job application initialized successfully for CandidateId: {candidate_id}, JobId: {job_id}."

        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": message,
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
