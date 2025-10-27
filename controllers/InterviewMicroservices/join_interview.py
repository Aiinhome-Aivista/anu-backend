from flask import request, jsonify
from database.db_handler import get_db_connection
from datetime import timedelta


def candidate_join_interview():
    try:
        # Parse input JSON
        data = request.get_json()
        job_id = data.get("jobid")
        candidate_id = data.get("candidateid")

        # Validate required parameters
        if not all([job_id, candidate_id]):
            return jsonify({
                "isSuccess": False,
                "message": "Missing required fields: jobid or candidateid",
                "status": "error",
                "statusCode": 400
            }), 400

        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch booked slot for the given job and candidate
        cursor.execute("""
            SELECT date, timeSlot, startTime, endTime
            FROM hiringmanagerselectedslots
            WHERE jobid = %s AND candidateId = %s AND isBooked = 1
        """, (job_id, candidate_id))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        meet_link = "https://meet.google.com/bpq-mjdk-wqt"

        # Helper to format timedelta to HH:MM:SS
        def format_time(value):
            if isinstance(value, timedelta):
                total_seconds = int(value.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            return str(value)

        result = []
        for row in rows:
            result.append({
                "date": str(row["date"]),
                "timeSlot": row["timeSlot"],
                "startTime": format_time(row["startTime"]),
                "endTime": format_time(row["endTime"]),
                "meetLink": meet_link
            })

        # If no data found → isSuccess = False
        if not result:
            return jsonify({
                "isSuccess": False,
                "message": "No slot found for the given candidate and job.",
                "result": [],
                "status": "error",
                "statusCode": 404
            }), 200

        # Success response
        return jsonify({
            "isSuccess": True,
            "message": "Data fetched successfully",
            "result": result,
            "status": "success",
            "statusCode": 200
        }), 200

    except Exception as e:
        return jsonify({
            "isSuccess": False,
            "message": str(e),
            "status": "error",
            "statusCode": 500
        }), 500