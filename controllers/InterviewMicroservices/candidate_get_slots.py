from datetime import datetime, timedelta
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

        # Step 2: Define the global date (next day of current date)
        current_date = datetime.now().date()
        global_date = current_date + timedelta(days=1)

        # Step 3: Fetch available slots from that global date onwards
        cursor.execute("""
            SELECT id, date, timeSlot, startTime, endTime
            FROM hiringmanagerselectedslots
            WHERE hiringManagerId = %s 
              AND isBooked = 0 
              AND date >= %s
            ORDER BY date, startTime
        """, (hiring_manager_id, global_date))

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

        # Step 4: Prepare recommended slots
        recommended_slots = [
            {
                "id": slot["id"],
                "date": str(slot["date"]),
                "timeSlot": slot["timeSlot"],
                "startTime": format_time(slot["startTime"]),
                "endTime": format_time(slot["endTime"])
            }
            for slot in slots
        ]

        # Step 5: If no slots available, return proper validation message
        if not recommended_slots:
            return jsonify({
                "isSuccess": False,
                "message": "No Slots Available.",
                "status": "error",
                "statusCode": 404,
                "candidateId": candidate_id,
                "jobid": job_id,
                "hiringManagerId": hiring_manager_id,
                "globalDate": str(global_date)
            }), 404

        # Step 6: Return successful response
        return jsonify({
            "candidateId": candidate_id,
            "jobid": job_id,
            "hiringManagerId": hiring_manager_id,
            "isSuccess": True,
            "message": "Data fetched successfully.",
            "recommendedSlots": recommended_slots,
            "status": "success",
            "statusCode": 200,
            "timezone": "IST",
            "globalDate": str(global_date),
            "totalSlots": len(recommended_slots)
        }), 200

    except Exception as e:
        return jsonify({
            "isSuccess": False,
            "message": str(e),
            "status": "error",
            "statusCode": 500
        }), 500
