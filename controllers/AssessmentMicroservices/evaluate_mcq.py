from flask import request,jsonify
from database.db_handler import get_db_connection

def evaluate_mcq():
    try:
        data = request.get_json()

        # Validate request body
        if not data or "JobId" not in data or "CandidateId" not in data or "Data" not in data:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "Invalid input data. 'JobId', 'CandidateId', and 'Data' are required.",
                "isSuccess": False
            }), 400

        jobId = data["JobId"]
        candidateId = data["CandidateId"]
        mcq_data = data["Data"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch MCQ data from the database
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

        # Calculate correct answers
        total_questions = len(mcq_data)
        correct_answers = 0

        for item in mcq_data:
            question = next((mcq for mcq in db_mcqs if mcq["Id"] == item["Id"]), None)
            if question and question["CorrectOption"] == item["SelectedOption"]:
                correct_answers += 1

        # Calculate percentage
        percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

        # Fetch threshold rule
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

        # Determine pass/fail
        status = "PASSED" if percentage >= rule_value else "FAILED"
        score = int(percentage) if status == "PASSED" else None

        # Call stored procedure (same as C#)
        cursor.callproc("UpdateProfileJourneyStatus", [
            jobId,
            candidateId,
            "ASSESSMENT",
            status,
            score
        ])
        conn.commit()

        # Success response
        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": "Evaluation completed successfully.",
            "isSuccess": True,
            "result": {
                "C_ID": candidateId,
                "J_ID": jobId,
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

