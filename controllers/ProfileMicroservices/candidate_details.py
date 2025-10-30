from flask import request, jsonify
from database.db_handler import get_db_connection
import json
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
        cursor = conn.cursor(dictionary=True,buffered=True)

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
            
            
        #  Fetch AI Screening Score & Details
            cursor.execute("""
                SELECT score, question_answer
                FROM assessment_session_log
                WHERE candidate_id = %s AND job_id = %s
            """, (candidate_id, jobId))
            aiscreening = cursor.fetchone()
            if aiscreening:
                candidate["aiscreening_score"] = f"{aiscreening['score']}%"
                raw_details = aiscreening.get("question_answer")
                # Safely parse the JSON string from DB
            if raw_details:
                try:
                    candidate["screening_details"] = json.loads(raw_details)
                except json.JSONDecodeError:
                    candidate["screening_details"] = []
            else:
                candidate["screening_details"] = []
        else:
            candidate["aiscreening_score"] = None
            candidate["screening_details"] = []


      # Step 4: Fetch Assessment score
        cursor.execute("""
            SELECT score AS assessment_score
            FROM jobassessments
            WHERE candidateId = %s AND jobId = %s AND assessmentName = 'Assessment'
        """, (candidate_id, jobId))
        assessment = cursor.fetchone()

        if assessment:
            candidate["assessment_score"] = f"{assessment['assessment_score']}%"

            # Step 5: Fetch all question details
            cursor.execute("""
                SELECT 
                    q.question,
                    a.selectedOption,
                    q.correctOption
                FROM assessmentinfo a
                JOIN jdbasedaimcq q ON a.questionNo = q.id
                WHERE a.candidateId = %s AND a.jobId = %s
            """, (candidate_id, jobId))
            rows = cursor.fetchall()

            # Add serial questionNo
            assessment_details = []
            for i, row in enumerate(rows, start=1):
                assessment_details.append({
                    "questionNo": i,
                    "question": row["question"],
                    "selectedOption": row["selectedOption"],
                    "correctOption": row["correctOption"]
                })

            candidate["assessment_details"] = assessment_details
        else:
            candidate["assessment_score"] = None
            candidate["assessment_details"] = []





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