import os
import re
import json
import requests
from flask import jsonify
from dotenv import load_dotenv
from database.db_handler import get_db_connection
from llm_utils import get_mistral_config, ACTIVE_LLM
import google.generativeai as genai

load_dotenv()


# -------------------------------
# Utility Function: Fuzzy Match Percentage
# -------------------------------
# def calculate_match_percentage(candidate_skills, job_skills):
#     candidate_list = [s.strip().lower() for s in candidate_skills.split(',') if s.strip()]
#     job_list = [s.strip().lower() for s in job_skills.split(',') if s.strip()]
#     if not candidate_list or not job_list:
#         return 0.0
#     match_count = sum(1 for c in candidate_list for j in job_list if c in j or j in c)
#     percentage = (match_count / len(job_list)) * 100
#     # Ensure percentage does not exceed 100
#     return round(min(percentage, 100.0), 2)


def calculate_match_percentage(candidate_skills, job_skills):
    """
    Uses Mistral Small model API to calculate skill match percentage.
    Returns a float (e.g. 78.5)
    """
    try:
        prompt = f"""
        You are an expert recruiter. 
        Calculate how well the candidate's skills match the job's required skills.
        Give ONLY a numeric percentage (0-100) with no text explanation.

        Candidate Skills: {candidate_skills}
        Job Required Skills: {job_skills}
        """

        if ACTIVE_LLM == "gemini":
            model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-3.6-flash"))
            response = model.generate_content(prompt)
            raw_output = response.text.strip()
        else:
            config = get_mistral_config()
            payload = {
                "model": config["model"],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "stream": False
            }

            print(f"Calling Mistral API URL: {config['url']}")
            response = requests.post(config["url"], headers=config["headers"], json=payload)
            response.raise_for_status()

            result = response.json()
            
            if "choices" in result:
                raw_output = result["choices"][0]["message"]["content"].strip()
            elif "message" in result:
                raw_output = result["message"]["content"].strip()
            elif "response" in result:
                raw_output = result["response"].strip()
            else:
                print(f"Unexpected API response format: {result}")
                return 0.0

        # Extract only numeric part (e.g. “85%” or “85.3”)
        match = re.search(r"(\d+(\.\d+)?)", raw_output)
        if match:
            return round(float(match.group(1)), 2)
        else:
            return 0.0

    except Exception as e:
        print("⚠️ Mistral API error:", e)
        return 0.0

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
    print(f"--- Starting match_jobs for candidate_id: {candidate_id} ---")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True,buffered=True)

        # Step 1: Fetch candidate skills
        cursor.execute("SELECT skills FROM candidateprofile WHERE id = %s", (candidate_id,))
        candidate = cursor.fetchone()
        if not candidate:
            print(f"Candidate {candidate_id} not found.")
            return jsonify({
                "isSuccess": False,
                "message": f"No candidate found with id {candidate_id}",
                "result": {},
                "status": "failed",
                "statusCode": 404
            })

        candidate_skills = candidate["skills"]
        print(f"Candidate skills fetched: {candidate_skills}")

        # Step 2: Fetch all jobs
        cursor.execute("SELECT id, primarySkills, jd FROM job")
        jobs = cursor.fetchall()

        if not jobs:
            print("No jobs found in the database.")
            return jsonify({
                "isSuccess": False,
                "message": "No jobs found in the database",
                "result": {},
                "status": "failed",
                "statusCode": 404
            })

        matched_jobs = []
        print(f"Total jobs fetched: {len(jobs)}")

        # Step 3: Process each job
        for job in jobs:
            print(f"\nProcessing Job ID: {job['id']}")
            match_percentage = calculate_match_percentage(candidate_skills, job["primarySkills"]
            )
            print(f"Match percentage for Job ID {job['id']}: {match_percentage}%")
            # print("candidate",candidate_skills)
            # print("job",job["primarySkills"])
            if match_percentage > 0:
                job_title, job_location = parse_jd(job["jd"])

                # Check if already exists in jobapplication
                cursor.execute("""
                    SELECT LatestStatus, jobmatchscore  FROM jobapplication 
                    WHERE candidateId = %s AND jobId = %s
                """, (candidate_id, job["id"]))
                existing = cursor.fetchone()

                if not existing:
                    # Insert only once (score included)
                    print(f"Inserting new job application for candidate {candidate_id} and Job {job['id']} with match {match_percentage}%")
                    cursor.execute("""
                        INSERT INTO jobapplication (candidateId, jobId, LatestStatus, jobmatchscore)
                        VALUES (%s, %s, 'Inactive',%s)
                    """, (candidate_id, job["id"], match_percentage))
                    conn.commit()
                    latest_status = "Inactive"
                else:
                    latest_status = existing["LatestStatus"]
                    match_percentage = existing.get("jobmatchscore", 0.0)
                    print(f"Job application already exists. Status: {latest_status}, Match: {match_percentage}%")

                matched_jobs.append({
                    "Id": job["id"],
                    "Title": job_title,
                    "match_percentage": f"{match_percentage}%",
                    "location": job_location,
                    "status": latest_status
                })

        # Step 4: Return response
        if matched_jobs:
            print(f"Successfully processed {len(matched_jobs)} matching jobs.")
            return jsonify({
                "isSuccess": True,
                "message": "Matching jobs processed successfully.",
                "result": matched_jobs,
                "status": "success",
                "statusCode": 200
            })
        else:
            print("No matching jobs found for candidate.")
            return jsonify({
                "isSuccess": False,
                "message": "No matching jobs found for candidate.",
                "result": {},
                "status": "failed",
                "statusCode": 404
            })

    except Exception as e:
        print(f"Error in match_jobs: {str(e)}")
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