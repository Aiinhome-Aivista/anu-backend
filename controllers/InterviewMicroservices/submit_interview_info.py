from flask import request, jsonify
from database.db_handler import get_db_connection
import mysql.connector

# ---------------------------
# POST API: submitInterviewInfo
# ---------------------------
def submit_interview_info():
    try:
        # Parse JSON payload
        payload = request.get_json(force=True)

        job_id = payload.get('jobId')
        candidate_id = payload.get('candidateId')
        join_status = payload.get('joinStatus')
        feedback = payload.get('feedback')
        selection_status = payload.get('selectionStatus')

        # Validation check
        if not all([job_id, candidate_id, join_status, feedback, selection_status]):
            return jsonify({
                "isSuccess": False,
                "message": "Missing required fields",
                "statusCode": 400
            }), 400

        # Strip spaces to avoid mismatch
        selection_status = selection_status.strip()

        # Map selection_status to score (only for valid statuses)
        score_map = {
            'Selected': 85,
            'Rejected': 25,
            'Under Review': 50
        }

        # DB connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Step 1: Insert into interviewinfo
        insert_query = """
            INSERT INTO interviewinfo 
            (JobId, CandidateId, JoinStatus, Feedback, SelectionStatus)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (job_id, candidate_id, join_status, feedback, selection_status))

        # Step 2: Update jobassessments table only if selection_status is valid
        assessment_sqnc = 3
        assessment_name = 'Teams Interview'

        if selection_status in score_map:
            score_value = score_map[selection_status]

            update_query = """
                UPDATE jobassessments
                SET status = 'Completed', score = %s
                WHERE jobId = %s
                  AND candidateId = %s
                  AND assessmentSqnc = %s
                  AND assessmentName = %s
            """
            cursor.execute(update_query, (score_value, job_id, candidate_id, assessment_sqnc, assessment_name))
            update_message = f"Job assessment updated successfully with score {score_value}" if cursor.rowcount > 0 else "No matching jobassessment found to update"
        else:
            update_message = "Selection status not valid, score not updated"

        # Commit both operations
        conn.commit()

        return jsonify({
            "isSuccess": True,
            "message": f"Interview info submitted successfully.",
            "status": "success",
            "statusCode": 200
        })

    except mysql.connector.Error as db_err:
        return jsonify({
            "isSuccess": False,
            "message": f"MySQL Error: {str(db_err)}",
            "statusCode": 500
        }), 500

    except Exception as e:
        return jsonify({
            "isSuccess": False,
            "message": f"Error: {str(e)}",
            "statusCode": 500
        }), 500

    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except:
            pass
