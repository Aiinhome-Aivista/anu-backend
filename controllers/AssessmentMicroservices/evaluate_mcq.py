from flask import request, jsonify
from database.db_handler import get_db_connection

def evaluate_mcq():
    try:
        data = request.get_json()

        # ✅ Validate request body
        required_keys = ["jobId", "candidateId", "assessmentId", "data"]
        if not data or not all(key in data for key in required_keys):
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "Invalid input data. 'jobId', 'candidateId', 'assessmentId', and 'data' are required.",
                "isSuccess": False
            }), 400

        jobId = data["jobId"]
        candidateId = data["candidateId"]
        assessmentId = data["assessmentId"]
        mcq_data = data["data"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # ✅ Fetch MCQ data for this job
        cursor.execute("""
            SELECT *
            FROM jdbasedaimcq
            WHERE JobId = %s
        """, (jobId,))
        db_mcqs = cursor.fetchall()

        if not db_mcqs:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": f"No MCQ data found for JobId {jobId}.",
                "isSuccess": False
            }), 404

        # ✅ Calculate correct answers
        total_questions = len(mcq_data)
        correct_answers = 0

        for item in mcq_data:
            question = next((mcq for mcq in db_mcqs if mcq["id"] == item["id"]), None)
            if question and question["correctOption"].strip().lower() == item["selectedOption"].strip().lower():
                correct_answers += 1

        percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

        # ✅ Fetch threshold rule
        cursor.execute("""
            SELECT RuleValue 
            FROM genericthreshold 
            WHERE RuleName = 'Shortlist Candidates'
            LIMIT 1
        """)
        threshold = cursor.fetchone()

        if not threshold:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": "Threshold rule 'Shortlist Candidates' not found.",
                "isSuccess": False
            }), 404

        try:
            rule_value = float(threshold["RuleValue"])
        except ValueError:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": f"Unable to parse RuleValue: {threshold['RuleValue']}",
                "isSuccess": False
            }), 400

        # ✅ Determine pass/fail
        status = "PASSED" if percentage >= rule_value else "FAILED"
        score = int(percentage)

        # ✅ Call stored procedure (added AssessmentId as 5th parameter)
        cursor.callproc("UpdateProfileJourneyStatus", [
            jobId,
            candidateId,
            "ASSESSMENT",
            status,
            score,
            assessmentId
        ])
        conn.commit()

        # ✅ Success response
        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": "Evaluation completed successfully.",
            "isSuccess": True,
            "result": {
                "C_ID": candidateId,
                "J_ID": jobId,
                "A_ID": assessmentId,
                "EVENT": "ASSESSMENT",
                "STATUS": status,
                "SCORE": score
            }
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