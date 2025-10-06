from flask import request, jsonify
from database.db_handler import get_db_connection

def login_candidate():
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

        cursor.execute("SELECT * FROM applicationuser WHERE Email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": "Login failed. Email not found.",
                "isSuccess": False
            }), 404

        if str(user.get("IsHiringManager")) == "0":
            return jsonify({
                "status": "success",
                "statusCode": 200,
                "message": "Login successful.",
                "isSuccess": True,
                "result": user
            }), 200

        return jsonify({
            "status": "failed",
            "statusCode": 401,
            "message": "Login failed. User is not a candidate.",
            "isSuccess": False
        }), 401

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
