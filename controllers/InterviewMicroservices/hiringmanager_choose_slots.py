from flask import Flask, request, jsonify
from database.db_handler import get_db_connection
from datetime import datetime




def add_hiring_manager_slots():
    try:
        data = request.get_json()
        hiring_manager_id = data.get("hiringManagerId")
        selected_slots = data.get("selectedSlots", [])
        timezone = data.get("timezone", "IST")
        created_by = hiring_manager_id  # default creator
        
        if not hiring_manager_id or not selected_slots:
            return jsonify({
                "isSuccess": False,
                "message": "Missing required fields: hiringManagerId or selectedSlots",
                "status": "error",
                "statusCode": 400
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO adani_talent.hiringmanagerselectedslots
            (hiringManagerId, date, timeSlot, startTime, endTime, isBooked, candidateId, createdBy)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        for slot in selected_slots:
            cursor.execute(insert_query, (
                hiring_manager_id,
                slot.get("date"),
                slot.get("timeSlot"),
                slot.get("startTime"),
                slot.get("endTime"),
                0,          # isBooked default
                None,       # candidateId default
                created_by
            ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "isSuccess": True,
            "message": f"{len(selected_slots)} slot(s) successfully added for {hiring_manager_id}.",
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



