from flask import request, jsonify
from database.db_handler import get_db_connection

def candidate_details():
    try:
        data = request.get_json()
        if not data or "Email" not in data:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "Email is required.",
                "isSuccess": False
            }), 400

        email = data["Email"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM candidateprofile WHERE email = %s", (email,))
        candidate = cursor.fetchone()

        if not candidate:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": "Candidate not found.",
                "isSuccess": False
            }), 404

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
