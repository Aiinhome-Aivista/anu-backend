import re
import json
from flask import jsonify
from database.db_handler import get_db_connection


# -------------------------------
# Utility Function: Fuzzy Match Percentage
# -------------------------------
def calculate_match_percentage(candidate_skills, job_skills):
    candidate_list = [s.strip().lower() for s in candidate_skills.split(',') if s.strip()]
    job_list = [s.strip().lower() for s in job_skills.split(',') if s.strip()]
    if not candidate_list or not job_list:
        return 0.0
    match_count = sum(1 for c in candidate_list for j in job_list if c in j or j in c)
    percentage = (match_count / len(job_list)) * 100
    # Ensure percentage does not exceed 100
    return round(min(percentage, 100.0), 2)


# -------------------------------
# JD Parsing Utility
# -------------------------------
def parse_jd(jd_text):
    job_title = ""
    job_location = ""
    if not jd_text:
        return job_title, job_location

    try:
        jd_data = json.loads(jd_text)
        job_title = jd_data.get("Job Title", "")
        job_location = jd_data.get("Location", "")
    except:
        pass

    return job_title, job_location


# -------------------------------
# Unified API → Match + Insert only (No update)
# -------------------------------
def match_jobs(candidate_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Step 1: Fetch candidate skills
        cursor.execute("SELECT skills FROM candidateprofile WHERE id = %s", (candidate_id,))
        candidate = cursor.fetchone()
        if not candidate:
            return jsonify({
                "isSuccess": False,
                "message": f"No candidate found with id {candidate_id}",
                "result": {},
                "status": "failed",
                "statusCode": 404
            })

        candidate_skills = candidate["skills"]

        # Step 2: Fetch all jobs
        cursor.execute("SELECT id, primarySkills, jd FROM job")
        jobs = cursor.fetchall()

        if not jobs:
            return jsonify({
                "isSuccess": False,
                "message": "No jobs found in the database",
                "result": {},
                "status": "failed",
                "statusCode": 404
            })

        matched_jobs = []

        # Step 3: Process each job
        for job in jobs:
            match_percentage = calculate_match_percentage(candidate_skills, job["primarySkills"])
            if match_percentage > 0:
                job_title, job_location = parse_jd(job["jd"])

                # Check if already exists in jobapplication
                cursor.execute("""
                    SELECT LatestStatus FROM jobapplication 
                    WHERE candidateId = %s AND jobId = %s
                """, (candidate_id, job["id"]))
                existing = cursor.fetchone()

                if not existing:
                    # Insert only once (score included)
                    cursor.execute("""
                        INSERT INTO jobapplication (candidateId, jobId, LatestStatus, Score)
                        VALUES (%s, %s, 'Inactive', %s)
                    """, (candidate_id, job["id"], match_percentage))
                    conn.commit()
                    latest_status = "Inactive"
                else:
                    latest_status = existing["LatestStatus"]

                matched_jobs.append({
                    "Id": job["id"],
                    "Title": job_title,
                    "match_percentage": f"{match_percentage}%",
                    "location": job_location,
                    "status": latest_status
                })

        # Step 4: Return response
        if matched_jobs:
            return jsonify({
                "isSuccess": True,
                "message": "Matching jobs processed successfully.",
                "result": matched_jobs,
                "status": "success",
                "statusCode": 200
            })
        else:
            return jsonify({
                "isSuccess": False,
                "message": "No matching jobs found for candidate.",
                "result": {},
                "status": "failed",
                "statusCode": 404
            })

    except Exception as e:
        return jsonify({
            "isSuccess": False,
            "message": str(e),
            "result": {},
            "status": "failed",
            "statusCode": 500
        })

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()