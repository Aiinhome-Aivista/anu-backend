from flask import Flask, jsonify
from database.db_handler import get_db_connection

def get_hiring_manager_slots(hiringManagerId):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT date, timeSlot, startTime, endTime, isBooked
            FROM hiringmanagerselectedslots
            WHERE hiringManagerId = %s
            ORDER BY date, startTime
        """
        cursor.execute(query, (hiringManagerId,))
        slots = cursor.fetchall()

        cursor.close()
        conn.close()

        if not slots:
            return jsonify({
                "hiringManagerId": hiringManagerId,
                "selectedSlots": [],
                "totalSlots": 0,
                "timezone": "IST",
                "isSuccess": True,
                "message": "No slots found for this hiring manager.",
                "status": "success",
                "statusCode": 200
            }), 200

        # Convert time fields to HH:MM
        def format_time(t):
            """Converts MySQL TIME field (timedelta or str) to HH:MM"""
            if isinstance(t, str):
                return t[:5]  # 'HH:MM:SS' → 'HH:MM'
            elif hasattr(t, 'seconds'):
                hours, remainder = divmod(t.seconds, 3600)
                minutes = remainder // 60
                return f"{hours:02d}:{minutes:02d}"
            else:
                return str(t)

        return jsonify({
            "hiringManagerId": hiringManagerId,
            "selectedSlots": [
                {
                    "date": str(slot["date"]),
                    "timeSlot": slot["timeSlot"],
                    "startTime": format_time(slot["startTime"]),
                    "endTime": format_time(slot["endTime"]),
                    "isBooked": slot["isBooked"],
                }
                for slot in slots
            ],
            "totalSlots": len(slots),
            "timezone": "IST",
            "isSuccess": True,
            "message": "Data fetched successfully.",
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


