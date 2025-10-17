from flask import request, jsonify
from database.db_handler import get_db_connection
from datetime import datetime
def evaluate_mcq():
    try:
        data = request.get_json()

        # Validate request body
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

        # Fetch MCQ data for this job
        cursor.execute("""
            SELECT *
            FROM jdbasedaimcq
            WHERE JobId = %s
        """, (jobId,))
        db_mcqs = cursor.fetchall()
        # print('db_mcqs:',db_mcqs)

        if not db_mcqs:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": f"No MCQ data found for JobId {jobId}.",
                "isSuccess": False
            }), 404

        #Calculate correct answers
        total_questions = len(mcq_data)
        # print('total_questions:',total_questions)
        correct_answers = 0

        for item in mcq_data:
            question = next((mcq for mcq in db_mcqs if mcq["id"] == item["id"]), None)
            if question:
                item_score = 5 if question["correctOption"].strip().lower() == item["selectedOption"].strip().lower() else 0
                item["score"] = item_score
                if item_score == 5:
                    correct_answers += 1

            # print('correct_answers:',correct_answers)

        percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        # print('percentage:',percentage)

        # #  Fetch threshold rule
        # cursor.execute("""
        #     SELECT RuleValue 
        #     FROM genericthreshold 
        #     WHERE RuleName = 'Shortlist Candidates'
        #     LIMIT 1
        # """)
        # threshold = cursor.fetchone()
        # # print('threshold:',threshold)

        # if not threshold:
        #     return jsonify({
        #         "status": "failed",
        #         "statusCode": 404,
        #         "message": "Threshold rule 'Shortlist Candidates' not found.",
        #         "isSuccess": False
        #     }), 404

        # try:
        #     rule_value = float(threshold["RuleValue"])
        # except ValueError:
        #     return jsonify({
        #         "status": "failed",
        #         "statusCode": 400,
        #         "message": f"Unable to parse RuleValue: {threshold['RuleValue']}",
        #         "isSuccess": False
        #     }), 400

        # Determine pass/fail
        # status = "PASSED" if percentage >= rule_value else "FAILED"
        status = "FAILED" if percentage <=45  else "PASSED"

        v_score = int(percentage)

        # Prepare insert data for assessmentinfo table
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Check if ANY record exists for this jobId + candidateId + assessmentId
        cursor.execute("""
            SELECT 1 FROM assessmentinfo
            WHERE jobId = %s AND candidateId = %s AND assessmentId = %s
            LIMIT 1
        """, (jobId, candidateId, assessmentId))

        record_exists = cursor.fetchone()

        if record_exists:
            #  UPDATE each question's record individually
            for item in mcq_data:
                question_id = item["id"]
                selected_option = item["selectedOption"]

                cursor.execute("""
                    UPDATE assessmentinfo
                    SET selectedOption = %s, score = %s, updatedAt = %s
                    WHERE jobId = %s AND candidateId = %s AND assessmentId = %s AND questionNo = %s
                """, (
                    selected_option, item["score"], now,
                    jobId, candidateId, assessmentId, question_id
                ))

        else:
            #  INSERT all rows
            insert_query = """
                INSERT INTO assessmentinfo (jobId, candidateId, assessmentId, questionNo, selectedOption, score, createdAt, updatedAt)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            insert_values = [
                (jobId, candidateId, assessmentId, item["id"], item["selectedOption"], item["score"], now, now)
                for item in mcq_data
            ]

            cursor.executemany(insert_query, insert_values)

        conn.commit()
        # print('status:',status)
        # print('score:',score)

        #  Call stored procedure (added AssessmentId as 5th parameter)
        cursor.callproc("UpdateProfileJourneyStatus", [
            jobId,
            candidateId,
            "ASSESSMENT",
            status,
            v_score,
            assessmentId
        ])
        conn.commit()

        #  Success response
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
                "SCORE": v_score
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