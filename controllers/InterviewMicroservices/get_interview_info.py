from flask import jsonify
from database.db_handler import get_db_connection


def get_interview_info(jobId, candidateId):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)

        query = """
            SELECT JobId, CandidateId, JoinStatus, Feedback, SelectionStatus
            FROM interviewinfo
            WHERE JobId = %s AND CandidateId = %s
        """
        cursor.execute(query, (jobId, candidateId))
        record = cursor.fetchone()

        cursor.close()
        conn.close()

        if not record:
            return jsonify({
                "isSuccess": False,
                "message": "No interview info found for given jobId and candidateId",
                "status": "failed",
                "statusCode": 404
            }), 404

        return jsonify({
            "isSuccess": True,
            "message": "Interview info fetched successfully.",
            "JobId": record['JobId'],
            "CandidateId": record['CandidateId'],
            "JoinStatus": record['JoinStatus'],
            "Feedback": record['Feedback'],
            "SelectionStatus": record['SelectionStatus'],
            "status": "success",
            "statusCode": 200
        }), 200

    except Exception as e:
        return jsonify({
            "isSuccess": False,
            "message": str(e),
            "status": "failed",
            "statusCode": 500
        }), 500







