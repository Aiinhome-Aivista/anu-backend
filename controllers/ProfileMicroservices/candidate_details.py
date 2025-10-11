from flask import request, jsonify
from database.db_handler import get_db_connection

def candidate_details():
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

        # Step 2: Fetch match percentage (Score) from jobapplication table
        cursor.execute("""
            SELECT AVG(Score) AS avg_score
            FROM jobapplication
            WHERE candidateId = %s
        """, (candidate_id,))
        score_data = cursor.fetchone()

        match_percentage = round(score_data["avg_score"], 2) if score_data and score_data["avg_score"] is not None else 0.0

        # Step 3: Add match_percentage to candidate data
        candidate["match_percentage"] = f"{match_percentage}%"

        # Step 4: Return response
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
            if conn.is_connected():
                cursor.close()
                conn.close()
        except:
            pass
