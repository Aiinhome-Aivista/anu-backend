import json
import random
from datetime import datetime
from flask import request, jsonify
from database.db_handler import get_db_connection


def calculate_score(answers, candidate_skills=None):
    if not answers or len(answers) == 0:
        return 0

    first_answer = answers[0]
    if isinstance(first_answer, dict):
        non_empty_answers = [ans for ans in answers if ans.get("answer", "").strip()]
    else:
        non_empty_answers = [a for a in answers if str(a).strip()]

    count = len(non_empty_answers)

    if count == 3:
         score = 50
    elif count < 3:
        score = random.randint(1, 49)
    else:
        score = random.randint(51, 100)


    return score


def end_interview():
    conn = None
    cursor = None

    try:
        data = request.get_json()

        candidate_id = data.get("candidateId")
        job_id = data.get("jobId")
        session_id = data.get("sessionId")
      
        # Validate input
        if not candidate_id or not job_id or not session_id:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "Invalid input. Required: candidateId, jobId, sessionId.",
                "isSuccess": False
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if session exists
        cursor.execute("""
            SELECT * FROM assessment_session_log
            WHERE candidate_id = %s AND job_id = %s AND session_id = %s
            ORDER BY created_at DESC LIMIT 1
        """, (candidate_id, job_id, session_id))
        session_row = cursor.fetchone()

        if not session_row:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": "Session not found.",
                "isSuccess": False
            }), 404

        current_status = session_row["status"]

        # If already ended, don't update again
        if current_status == "ended":
            return jsonify({
                "status": "success",
                "statusCode": 200,
                "message": f"Interview already ended for candidate {candidate_id}.",
                "isSuccess": True,
                "result": {
                    "candidateId": candidate_id,
                    "jobId": job_id,
                    "sessionId": session_id,
                    "interviewStatus": "ended",
                    "score": session_row.get("score", None)
                }
            }), 200

        # If active, calculate score and mark as ended
        if current_status == "active":
            answers_data = session_row.get("question_answer")

            # Convert JSON string from DB into Python list (if not None)
            if isinstance(answers_data, str):
                try:
                    answers = json.loads(answers_data)
                except json.JSONDecodeError:
                    answers = []
            else:
                answers = answers_data or []
            score = calculate_score(answers)

            cursor.execute("""
                UPDATE assessment_session_log
                SET status = %s, ended_at = %s, score = %s
                WHERE id = %s
            """, ("ended", datetime.now(), score, session_row["id"]))
            conn.commit()

            return jsonify({
                "status": "success",
                "statusCode": 200,
                "message": "Your interview has been successfully ended. Thank you for your participation!",
                "isSuccess": True,
                "result": {
                    "candidateId": candidate_id,
                    "jobId": job_id,
                    "sessionId": session_id,
                    "interviewStatus": "ended",
                    "score": score
                }
            }), 200

        # If in any other status (pending, paused, etc.), handle gracefully
        return jsonify({
            "status": "failed",
            "statusCode": 409,
            "message": f"Interview cannot be ended because current status is '{current_status}'.",
            "isSuccess": False
        }), 409

    except Exception as e:
        return jsonify({
            "status": "failed",
            "statusCode": 500,
            "message": str(e),
            "isSuccess": False
        }), 500

    finally:
        try:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
        except:
            pass
