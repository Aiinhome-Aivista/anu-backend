import json  
from flask import jsonify
from database.db_handler import get_db_connection


def job_description(candidate_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT jd FROM job WHERE id = %s", (candidate_id,))
        result = cursor.fetchone()

        if result:
            #  Convert JSON string to dict
            try:
                jd_data = json.loads(result["jd"])
            except Exception:
                jd_data = result["jd"]  

            return jsonify({
                "isSuccess": True,
                "message": f"Job description fetched successfully for candidate_id {candidate_id}.",
                "jd": jd_data,  
                "status": "success",
                "statusCode": 200
            })
        else:
            return jsonify({
                "isSuccess": False,
                "message": f"No job found for candidate_id {candidate_id}.",
                "jd": None,
                "status": "failed",
                "statusCode": 404
            })

    except Exception as e:
        return jsonify({
            "isSuccess": False,
            "message": str(e),
            "jd": None,
            "status": "failed",
            "statusCode": 500
        })

    finally:
        try:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
        except:
            pass


