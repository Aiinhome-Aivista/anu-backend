from flask import Flask, request, jsonify
from database.db_handler import get_db_connection



def get_recommended_slots():
    try:
        data = request.get_json()
        candidate_id = data.get("candidateId")
        job_id = data.get("jobid")

        if not candidate_id or not job_id:
            return jsonify({
                "isSuccess": False,
                "message": "Missing required fields: candidateId or jobid",
                "status": "error",
                "statusCode": 400
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Step 1: Get hiringManagerId from job table
        cursor.execute("SELECT hiringManagerId FROM job WHERE id = %s", (job_id,))
        job_row = cursor.fetchone()

        if not job_row or not job_row["hiringManagerId"]:
            cursor.close()
            conn.close()
            return jsonify({
                "isSuccess": False,
                "message": f"No hiring manager found for job ID {job_id}",
                "status": "error",
                "statusCode": 404
            }), 404

        hiring_manager_id = job_row["hiringManagerId"]

        # Step 2: Fetch available slots for this hiring manager
        cursor.execute("""
            SELECT id, date, timeSlot, startTime, endTime
            FROM hiringManagerSelectedSlots
            WHERE hiringManagerId = %s AND isBooked = 0
            ORDER BY date, startTime
        """, (hiring_manager_id,))
        slots = cursor.fetchall()

        cursor.close()
        conn.close()

        # Helper function to convert TIME → HH:MM
        def format_time(t):
            if isinstance(t, str):
                return t[:5]
            elif hasattr(t, 'seconds'):
                hours, remainder = divmod(t.seconds, 3600)
                minutes = remainder // 60
                return f"{hours:02d}:{minutes:02d}"
            else:
                return str(t)

        recommended_slots = [
            {"id": slot["id"],
                "date": str(slot["date"]),
                "timeSlot": slot["timeSlot"],
                "startTime": format_time(slot["startTime"]),
                "endTime": format_time(slot["endTime"])
            }
            for slot in slots
        ]

        return jsonify({
            "candidateId": candidate_id,
            "jobid": job_id,
            "hiringManagerId": hiring_manager_id,
            "isSuccess": True,
            "message": "Data fetched successfully." if slots else "No available slots found.",
            "recommendedSlots": recommended_slots,
            "status": "success",
            "statusCode": 200,
            "timezone": "IST",
            "totalSlots": len(recommended_slots)
        }), 200

    except Exception as e:
        return jsonify({
            "isSuccess": False,
            "message": str(e),
            "status": "error",
            "statusCode": 500
        }), 500


