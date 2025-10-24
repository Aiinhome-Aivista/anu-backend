from flask import Flask, jsonify
from database.db_handler import get_db_connection
import json




def job_search():
    try:
      
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        
        cursor.execute("SELECT id, jd FROM job")
        rows = cursor.fetchall()
        
        result = []
        
        for row in rows:
            try:
                jd_data = json.loads(row['jd'])
                job_title = jd_data.get("Job Title", None)
            except (json.JSONDecodeError, TypeError):
                job_title = None
            
            result.append({
                "job_id": row['id'],
                "Job Title": job_title
            })
        
        cursor.close()
        conn.close()

        return jsonify({
            "status": "Success",
            "statusCode": 200,
            "message": "Data fetched successfully.",
            "isSuccess": True,
            "result": result
        })

    except Exception as e:
        print("Error:", e)
        return jsonify({
            "status": "Error",
            "statusCode": 500,
            "message": str(e),
            "isSuccess": False,
            "result": []
        }), 500


