import os
import json
import random
import requests
from datetime import datetime
from flask import request, jsonify
from database.db_handler import get_db_connection
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_API_URL = os.getenv("MISTRAL_API_URL")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL")


def get_ai_score(question_answer):
    try:
        #  Handle empty or missing data — return 0
        if not question_answer or len(question_answer) == 0:
            return 0

        #  Detect meaningful (non-empty) answers
        non_empty_answers = []
        if isinstance(question_answer, list):
            for qa in question_answer:
                ans_text = ""
                if isinstance(qa, dict):
                    ans_text = qa.get("answer", "").strip()
                elif isinstance(qa, str):
                    ans_text = qa.strip()
                if ans_text:
                    non_empty_answers.append(qa)
        elif isinstance(question_answer, dict):
            for _, v in question_answer.items():
                if str(v).strip():
                    non_empty_answers.append(v)

        #  If no actual text answers, give 0
        if len(non_empty_answers) == 0:
            return 0

        #  Ensure Mistral environment vars exist
        if not MISTRAL_API_URL or not MISTRAL_API_KEY or not MISTRAL_MODEL:
            raise ValueError("Mistral API configuration missing in environment variables.")

        #  Create intelligent prompt for AI evaluation
        prompt = f"""
            You are an AI evaluation model integrated into an interview system.

            Analyze the candidate's interview responses carefully and provide a final performance score between 1 and 100.

            Candidate's answers (JSON):
            {json.dumps(non_empty_answers, ensure_ascii=False, indent=2)}

            Evaluation criteria:
            - Correctness and relevance of answers
            - Depth of explanation
            - Clarity of communication
            - Logical reasoning ability
            - Completeness of responses

            Scoring guideline:
            - 1–40 → Poor understanding or irrelevant responses
            - 41–60 → Average or partially correct answers
            - 61–80 → Good understanding and mostly correct
            - 81–100 → Excellent reasoning, deep knowledge, and clarity

            Return ONLY the final score as a single integer (1–100). Do not include text or explanation.
            """

        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": MISTRAL_MODEL,
            "messages": [
                {"role": "system", "content": "You are an intelligent evaluation model."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 10
        }

        response = requests.post(MISTRAL_API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code != 200:
            raise Exception(f"Mistral API error: {response.status_code} - {response.text}")

        result = response.json()
        ai_output = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

        #  Extract and sanitize numeric score from AI output
        try:
            score = int(''.join(filter(str.isdigit, ai_output)))
            if score < 1 or score > 100:
                score = random.randint(40, 60) 
        except:
            score = random.randint(40, 60)  

        return score

    except Exception as e:
        print(f"[Mistral Score Error] {str(e)}")
        #  Fallback score in case of API or parsing error
        return random.randint(40, 60)


def end_interview():
    conn = None
    cursor = None

    try:
        data = request.get_json()
        candidate_id = data.get("candidateId")
        job_id = data.get("jobId")
        session_id = data.get("sessionId")

        #  Validate input
        if not candidate_id or not job_id or not session_id:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "Invalid input. Required: candidateId, jobId, sessionId.",
                "isSuccess": False
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        #  Fetch the most recent session log
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

        #  If already ended, return existing score
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
                    "score": session_row.get("score", 0)
                }
            }), 200

        #  If active, evaluate and end
        if current_status == "active":
            answers_data = session_row.get("question_answer")

            # Convert JSON string from DB
            if isinstance(answers_data, str):
                try:
                    question_answer = json.loads(answers_data)
                except json.JSONDecodeError:
                    question_answer = []
            else:
                question_answer = answers_data or []

            #  Generate score dynamically
            score = get_ai_score(question_answer)

            #  Update DB with final score
            cursor.execute("""
                UPDATE assessment_session_log
                SET status = %s, ended_at = %s, score = %s
                WHERE id = %s
            """, ("ended", datetime.now(), score, session_row["id"]))
            conn.commit()

            #  Respond with success
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

        #  Invalid status case
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

