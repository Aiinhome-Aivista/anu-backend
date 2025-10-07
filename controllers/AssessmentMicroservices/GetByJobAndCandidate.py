from flask import request,jsonify
from database.db_handler import get_db_connection

def GetByJobAndCandidate(jobId, candidateId):
    try:
        if not jobId or not candidateId:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "Both jobId and candidateId are required.",
                "isSuccess": False
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * 
            FROM jobassessments
            WHERE JobId = %s AND CandidateId = %s
            ORDER BY AssessmentSqnc
        """, (jobId, candidateId))
        assessments = cursor.fetchall()

        if not assessments:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": "No records found.",
                "isSuccess": False,
                "result": None
            }), 404

        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": "Records retrieved successfully.",
            "isSuccess": True,
            "result": assessments
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

