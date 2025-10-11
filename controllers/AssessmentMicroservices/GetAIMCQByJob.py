import random
from flask import request,jsonify
from database.db_handler import get_db_connection

def GetAIMCQByJob(AID, jobId, CID):
    try:
        if not jobId:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "JobId is required.",
                "isSuccess": False
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        #  Fetch actual MCQs instead of assessments
        cursor.execute("""
            SELECT *
            FROM jdbasedaimcq
            WHERE JobId = %s
        """, (jobId,))

        mcq_list = cursor.fetchall()

        if not mcq_list:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": "No MCQ records found for the given JobId.",
                "isSuccess": False,
                "result": None
            }), 404

        random_mcqs=random.sample(mcq_list,min(5,len(mcq_list)))
        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": "MCQ records retrieved successfully.",
            "isSuccess": True,
            "result": random_mcqs
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