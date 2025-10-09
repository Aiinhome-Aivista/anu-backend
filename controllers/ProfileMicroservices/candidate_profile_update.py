from flask import request, jsonify
from database.db_handler import get_db_connection

def update_candidate():
    try:
        data = request.get_json()

        required_fields = ["id", "address", "latestrole", "education", "designation", "certification", "skills"]
        if not all(field in data for field in required_fields):
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "Missing required fields.",
                "isSuccess": False
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Call stored procedure
        cursor.callproc("UpdateCandidateProfile", (
            data["id"],
            data["address"],
            data["latestrole"],
            data["education"],
            data["designation"],
            data["certification"],
            data["skills"]
        ))

        conn.commit()

        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": "Candidate profile updated successfully.",
            "isSuccess": True
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
