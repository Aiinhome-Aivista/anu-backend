from flask import request, jsonify
from database.db_handler import get_db_connection

def candidate_details():
    conn = None
    cursor = None

    try:
        data = request.get_json()
        if not data or "email" not in data:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "email is required.",
                "isSuccess": False
            }), 400

        email = data["email"]
        jobId = data.get("jobId")  # Make jobId optional using get()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Step 1: Fetch candidate details
        cursor.execute("SELECT * FROM candidateprofile WHERE email = %s", (email,))
        candidate = cursor.fetchone()

        if not candidate:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": "Candidate not found.",
                "isSuccess": False
            }), 404

        candidate_id = candidate["id"]
        
        # Step 2: If jobId is provided, fetch job details and job match score
        if jobId:
            cursor.execute("SELECT * FROM jobapplication WHERE JobId = %s", (jobId,))
            jobapplication = cursor.fetchone()

            if not jobapplication:
                return jsonify({
                    "status": "failed",
                    "statusCode": 404,
                    "message": "Job not found.",
                    "isSuccess": False
                }), 404

            job_id = jobapplication["JobId"]

            # Fetch match percentage (Score) from jobapplication table
            cursor.execute("""
                SELECT jobmatchscore
                FROM jobapplication
                WHERE candidateId = %s AND JobId = %s
            """, (candidate_id, job_id))
            score_data = cursor.fetchone()

            match_percentage = (score_data["jobmatchscore"]
                                if score_data and score_data["jobmatchscore"] is not None else 0.0)
            candidate["match_percentage"] = f"{match_percentage}%"
        else:
            # If no jobId is provided, set match_percentage to None
            candidate["match_percentage"] = None


        # #  Fetch AI Screening Score & Details
        #     cursor.execute("""
        #         SELECT score, question_answer
        #         FROM assessment_session_log
        #         WHERE candidateId = %s AND jobId = %s
        #     """, (candidate_id, jobId))
        #     aiscreening = cursor.fetchone()
        #     if aiscreening:
        #         candidate["aiscreening_score"] = aiscreening["score"]
        #         candidate["screening_details"] = aiscreening["question_answer"]

        # #  Fetch Assessment Score & Details (with JOIN)
        #     cursor.execute("""
        #         SELECT 
        #             ja.score AS assessment_score,
        #             af.details AS assessment_details
        #         FROM jobassessments ja
        #         JOIN assessmentinfo af 
        #             ON s.candidateId = d.candidateId AND s.jobId = d.jobId
        #         WHERE s.candidateId = %s AND s.jobId = %s
        #     """, (candidate_id, jobId))

        #     assessment = cursor.fetchone()
        #     if assessment:
        #         candidate["assessment_score"] = assessment["assessment_score"]
        #         candidate["assessment_details"] = assessment["assessment_details"]




        # Step 3: Return response with candidate details
        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": "Candidate details retrieved successfully.",
            "isSuccess": True,
            "result": candidate
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
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
        except:
            pass