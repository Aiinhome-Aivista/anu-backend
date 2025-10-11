from flask import request, jsonify
from database.db_handler import get_db_connection


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

        # DB connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Insert query
        insert_query = """
            INSERT INTO interviewinfo 
            (JobId, CandidateId, JoinStatus, Feedback, SelectionStatus)
            VALUES (%s, %s, %s, %s, %s)
        """
        values = (job_id, candidate_id, join_status, feedback, selection_status)
        cursor.execute(insert_query, values)
        conn.commit()

        return jsonify({
            "isSuccess": True,
            "message": "Interview info submitted successfully",
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


