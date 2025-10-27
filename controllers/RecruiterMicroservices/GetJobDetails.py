from flask import Flask, request, jsonify
from database.db_handler import get_db_connection
import json
 

def fully_parse_json(value):
    """
    Recursively decode a JSON string until we get a dict/list.
    Handles multiple nested layers and cleans backslashes.
    """
    if isinstance(value, dict):
        return {k: fully_parse_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [fully_parse_json(v) for v in value]
    if isinstance(value, str):
        cleaned = value.strip().replace("```json", "").replace("```", "")
        for _ in range(10):  # decode multiple layers
            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, str):
                    cleaned = parsed
                    continue
                return fully_parse_json(parsed)
            except json.JSONDecodeError:
                # unescape manually if decoding fails
                cleaned = cleaned.encode("utf-8").decode("unicode_escape").replace('\\"', '"')
                break
        return cleaned
    return value

def extract_job_title_recursively(data):
    """Recursively search for 'Job Title' in a dict/list."""
    if isinstance(data, dict):
        for k, v in data.items():
            if k.lower() == "job title":
                return v
            result = extract_job_title_recursively(v)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = extract_job_title_recursively(item)
            if result:
                return result
    return None

def get_job_details():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT * FROM v_recruiter_job_details"
        cursor.execute(query)
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        if not rows:
            return jsonify({
                "status": "No Data Found",
                "statusCode": 404,
                "message": "No job details available.",
                "isSuccess": False,
                "result": []
            }), 404

        # Clean JD and extract JobTitle
        for row in rows:
            if "JD" in row:
                jd_clean = fully_parse_json(row["JD"])
                row["JD"] = jd_clean
                row["JobTitle"] = extract_job_title_recursively(jd_clean)

        return jsonify({
            "status": "Success",
            "statusCode": 200,
            "message": "Job details fetched successfully.",
            "isSuccess": True,
            "result": rows
        }), 200

    except Exception as e:
        return jsonify({
            "status": "Error",
            "statusCode": 500,
            "message": str(e),
            "isSuccess": False,
            "result": []
        }), 500

# def get_job_details():
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)

#         query = "SELECT * FROM v_recruiter_job_details"
#         cursor.execute(query)
#         rows = cursor.fetchall()

#         cursor.close()
#         conn.close()

#         if not rows:
#             return jsonify({
#                 "status": "No Data Found",
#                 "statusCode": 404,
#                 "message": "No job details available for the specified hiring managers.",
#                 "isSuccess": False,
#                 "result": []
#             }), 404

#         # 🧹 Clean up and properly parse nested JSON for each JD
#         for row in rows:
#             if "JD" in row and isinstance(row["JD"], str):
#                 row["JD"] = clean_json_value(row["JD"])

#         return jsonify({
#             "status": "Success",
#             "statusCode": 200,
#             "message": "Job details fetched successfully.",
#             "isSuccess": True,
#             "result": rows
#         }), 200

#     except Exception as e:
#         return jsonify({
#             "status": "Error",
#             "statusCode": 500,
#             "message": str(e),
#             "isSuccess": False,
#             "result": []
#         }), 500



# def get_job_details():
#     try:
#         # Get a database connection
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)

#         # Query the MySQL view
#         query = "SELECT * FROM v_recruiter_job_details"
#         cursor.execute(query)
#         rows = cursor.fetchall()

#         # Close connections
#         cursor.close()
#         conn.close()

#         # If no data found
#         if not rows:
#             return jsonify({
#                 "status": "No Data Found",
#                 "statusCode": 404,
#                 "message": "No job details available for the specified hiring managers.",
#                 "isSuccess": False,
#                 "result": []
#             }), 404

#         # Return successful response
#         return jsonify({
#             "status": "Success",
#             "statusCode": 200,
#             "message": "Job details fetched successfully.",
#             "isSuccess": True,
#             "result": rows
#         }), 200

#     except Exception as e:
#         # Handle exceptions
#         return jsonify({
#             "status": "Error",
#             "statusCode": 500,
#             "message": str(e),
#             "isSuccess": False,
#             "result": []
#         }), 500


def get_job_search():
    try:
        
        data = request.get_json()

        if not data or 'id' not in data:
            return jsonify({
                "status": "Bad Request",
                "statusCode": 400,
                "message": "Missing required parameter: id in request body",
                "isSuccess": False,
                "result": []
            }), 400

        job_id = data['id']

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query the MySQL view using the id
        query = """
            SELECT * 
            FROM v_recruiter_job_search
            WHERE Id = %s
        """
        cursor.execute(query, (job_id,))
        rows = cursor.fetchall()

        # Close connections
        cursor.close()
        conn.close()

        # If no data found
        if not rows:
            return jsonify({
                "status": "No Data Found",
                "statusCode": 404,
                "message": f"No job found for id: {job_id}",
                "isSuccess": False,
                "result": []
            }), 404

        # Success response
        return jsonify({
            "status": "Success",
            "statusCode": 200,
            "message": "Job search details fetched successfully.",
            "isSuccess": True,
            "result": rows
        }), 200

    except Exception as e:
        # Handle exceptions
        return jsonify({
            "status": "Error",
            "statusCode": 500,
            "message": str(e),
            "isSuccess": False,
            "result": []
        }), 500