from flask import request,jsonify
from database.db_handler import get_db_connection

def GetAIMCQByJob(AID, jobId, CID):
    try:
        # Validate input
        if not jobId:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "JobId is required.",
                "isSuccess": False
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch data where JobId matches
        cursor.execute("""
            SELECT * 
            FROM jobassessments
           WHERE Id = %s AND JobId = %s AND CandidateId = %s
        """, (AID, jobId, CID))

        mcq_list = cursor.fetchall()

        if not mcq_list:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": "No records found for the given JobId.",
                "isSuccess": False,
                "result": None
            }), 404

        # Return success response
        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": "MCQ records retrieved successfully.",
            "isSuccess": True,
            "result": mcq_list
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
            if conn:
                cursor.close()
                conn.close()
        except:
            pass

