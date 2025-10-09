import os
import uuid
import json
import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask, request, jsonify
from database.db_handler import get_db_connection

load_dotenv()
# ---------- Configure Gemini API Key ----------
Api_key=os.getenv("GEMINI_API_KEY")
genai.configure(api_key=Api_key)

# ---------- Utility: Clean Gemini JSON ----------
def fix_gemini_result(raw_response):
    """
    Unwraps and cleans Gemini JSON if it comes double-encoded.
    """
    try:
        if isinstance(raw_response.get("result"), str):
            raw_response["result"] = json.loads(raw_response["result"])
    except Exception:
        pass
    return raw_response

# ---------- Function 1: Generate Job Description ----------
def generate_job_description():
    try:
        data = request.get_json()

        job_title = data.get("jobTitle")
        job_experience = data.get("jobExperienceRequired")
        job_location = data.get("jobLocation")
        job_primary_skills = data.get("jobPrimarySkills", [])
        job_secondary_skills = data.get("jobSecondarySkills", [])
        job_edu_qualifications = data.get("jobEducationalQualifications", [])
        job_business_dependencies = data.get("jobBusinessDependencies")
        job_role = data.get("jobRole")
        job_type = data.get("jobType")

        # ---------- Generate JD using Gemini ----------
        prompt = f"""
        Generate a professional Job Description (max 100 words) for the following role.
        Ensure it’s detailed, concise, and relevant.

        Job Title: {job_title}
        Location: {job_location}
        Job Type: {job_type}
        Role: {job_role}
        Experience Required: {job_experience}
        Primary Skills: {', '.join(job_primary_skills)}
        Secondary Skills: {', '.join(job_secondary_skills)}
        Educational Qualifications: {', '.join(job_edu_qualifications)}
        Business Dependencies: {job_business_dependencies}

        ### Output Rules (follow exactly)
        - Respond ONLY with valid JSON — no markdown, code blocks, or explanations.
        - Do NOT wrap the whole JSON in quotes or escape characters.
        - The "result" field **must be a nested JSON object**, not a string.
        - Do not include backslashes (\\) or escaped quotes (\").
        - Example output format (copy structure exactly):

        {{
            "isSuccess": true,
            "message": "Data fetched successfully",
            "result": {{
                "Job Title": "Example",
                "Location": "Example",
                "Job Type": "Example",
                "Role": "Example",
                "Role Overview": "Example overview",
                "Key Responsibilities": ["..."],
                "Qualifications": ["..."],
                "Desired Skills": ["..."]
            }},
            "status": "success",
            "statusCode": 200
        }}
        """

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        job_description_text = response.text.strip()

        # ---------- Remove any code block markers ----------
        if job_description_text.startswith("```json"):
            job_description_text = job_description_text.replace("```json", "", 1).strip()
        if job_description_text.endswith("```"):
            job_description_text = job_description_text[:-3].strip()

        # ---------- Parse JSON safely ----------
        try:
            jd_json = json.loads(job_description_text)
        except json.JSONDecodeError:
            # fallback if Gemini returns plain text
            jd_json = {
                "isSuccess": True,
                "message": "Data fetched successfully",
                "result": {
                    "Job Title": job_title,
                    "Location": job_location,
                    "Job Type": job_type,
                    "Role": job_role,
                    "Role Overview": job_description_text,
                    "Key Responsibilities": [],
                    "Qualifications": [],
                    "Desired Skills": []
                },
                "status": "success",
                "statusCode": 200
            }

        # ---------- Fix double-encoded "result" ----------
        jd_json = fix_gemini_result(jd_json)

        # ---------- Optional: enforce 150-word limit on Role Overview ----------
        overview = jd_json.get("result", {}).get("Role Overview")
        if overview:
            words = overview.split()
            if len(words) > 150:
                jd_json["result"]["Role Overview"] = " ".join(words[:150]) + "..."

        # ---------- Return clean JSON response ----------
        return jsonify(jd_json)

    except Exception as e:
        return jsonify({
            "isSuccess": False,
            "message": f"Error: {str(e)}",
            "status": "failed",
            "statusCode": 500
        })


# ---------- Function 2: Create Job ----------
def create_job():
    try:
        data = request.get_json()

        job_title = data.get("jobTitle")
        job_experience = data.get("jobExperienceRequired")
        job_location = data.get("jobLocation")
        job_primary_skills = data.get("jobPrimarySkills", [])
        job_secondary_skills = data.get("jobSecondarySkills", [])
        job_edu_qualifications = data.get("jobEducationalQualifications", [])
        job_business_dependencies = data.get("jobBusinessDependencies")
        job_role = data.get("jobRole")
        job_type = data.get("jobType")
        job_hiring_manager = data.get("jobHiringManager")   # email
        job_description_text = data.get("jobDescriptionText")

        # ---------- Generate Unique Job GUID ----------
        j_guid = str(uuid.uuid4())
        created_by = job_hiring_manager

        # Ensure JD is a string (already stringified from generate_job_description)
        if not isinstance(job_description_text, str):
            jd_str = json.dumps(job_description_text, ensure_ascii=False)
        else:
            jd_str = job_description_text

        # ---------- Insert into Database ----------
        conn = get_db_connection()
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO adani_talent.job 
            (j_guid, jd, experience, location, role, primarySkills, secondarySkills, 
             businessDependencies, hiringManagerId, createdBy, createdOn)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, (
            j_guid,
            jd_str,  # store the clean string
            job_experience,
            job_location,
            job_role,
            json.dumps(job_primary_skills),
            json.dumps(job_secondary_skills),
            job_business_dependencies,
            job_hiring_manager,
            created_by,
            datetime.datetime.now().strftime("%Y-%m-%d")
        ))

        conn.commit()
        cursor.close()
        conn.close()

        # ---------- Response ----------
        return jsonify({
            "isSuccess": True,
            "message": "Job created successfully",
            "result": [data],
            "status": "success",
            "statusCode": 200
        })

    except Exception as e:
        return jsonify({
            "isSuccess": False,
            "message": f"Error: {str(e)}",
            "status": "failed",
            "statusCode": 500
        })
