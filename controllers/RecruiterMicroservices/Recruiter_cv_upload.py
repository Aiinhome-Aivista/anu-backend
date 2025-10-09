import os
import uuid
import json
import re
from flask import request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import google.generativeai as genai
import fitz  
from database.db_handler import get_db_connection

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(filepath):
    text = ""
    with fitz.open(filepath) as pdf:
        for page in pdf:
            text += page.get_text()
    return text

def recruiter_upload_cv():
    try:
        # Check if files exist in request
        if 'files' not in request.files:
            return jsonify({"error": "No files part"}), 400

        files = request.files.getlist('files')
        hiring_manager_id = request.form.get('HiringManagerId')
        job_id = request.form.get('job_id')

        if not files or len(files) == 0:
            return jsonify({"error": "No files selected"}), 400

        if not hiring_manager_id or not job_id:
            return jsonify({"error": "HiringManagerId and job_id are required"}), 400

        results = []

        for file in files:
            if not allowed_file(file.filename):
                results.append({
                    "filename": file.filename,
                    "status": "failed",
                    "reason": "Invalid file type"
                })
                continue

            # Save file
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            # Extract text
            if filename.lower().endswith(".pdf"):
                text_content = extract_text_from_pdf(filepath)
            else:
                text_content = "Non-PDF extraction not implemented"

            if not text_content.strip():
                results.append({
                    "filename": filename,
                    "status": "failed",
                    "reason": "Failed to extract data from CV"
                })
                continue

            # Generate JSON using Gemini
            model = genai.GenerativeModel("gemini-2.5-flash")  
            prompt = f"""
            You are a CV parsing assistant. 
            Analyze the following resume text and extract the information in a **clean JSON format** with the following exact keys:
            {{
                "title": "",
                "first_name": "",
                "middle_name": "",
                "last_name": "",
                "email": "",
                "contact": "",
                "address": "",
                "latestrole": "",
                "education": "",
                "designation": "",
                "certification": "",
                "skills": "",
                "experience": ""
            }}
            Instructions:
            1. Extract the most accurate details for each field.
            2. For *title*, determine it based on marital status or gender indicators:
            - Use *"Mr."* for male candidates.
            - Use *"Mrs."* for married female candidates.
            - Use *"Ms."* for unmarried female candidates or if marital status is unclear but name suggests female.
            - If gender cannot be determined, leave it empty.
            3. For "experience", **calculate or estimate the total professional experience in years**, using date ranges, durations, or job history if available.
            - If the end date is "Present" or "Current", calculate experience up to the current date.
            - If exact duration cannot be determined, return "None".
            - Example valid values for experience: "2 ", "3.5 ", or "None".
            - Do not include descriptive text in the experience field.
            4. Ensure JSON is valid and machine-readable.
            CV Text:
            {text_content}
            """

            response = model.generate_content(prompt)
            raw_text = response.text.strip() if response else "{}"

            # Parse Gemini output safely
            try:
                extracted_data = json.loads(raw_text)
            except json.JSONDecodeError:
                cleaned_text = re.sub(r"```(json|JSON)?", "", raw_text).strip("` \n")
                extracted_data = json.loads(cleaned_text or "{}")

            expected_keys = [
                "title", "first_name", "middle_name", "last_name", "email",
                "contact", "address", "latestrole", "education", "designation",
                "certification", "skills", "experience"
            ]
            for key in expected_keys:
                extracted_data.setdefault(key, "")

            c_guid = str(uuid.uuid4())

            # Insert into database
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = """
            INSERT INTO candidateprofile 
            (title, first_name, middle_name, last_name, email, contact, address,
             latestrole, education, designation, certification, skills, experience, C_GUID, ForDemo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Y')
            """
            values = (
                extracted_data["title"],
                extracted_data["first_name"],
                extracted_data["middle_name"],
                extracted_data["last_name"],
                extracted_data["email"] or "",
                extracted_data["contact"],
                extracted_data["address"],
                extracted_data["latestrole"],
                extracted_data["education"],
                extracted_data["designation"],
                extracted_data["certification"],
                extracted_data["skills"],
                extracted_data["experience"],
                c_guid
            )
            cursor.execute(sql, values)
            conn.commit()
            cursor.close()
            conn.close()

            results.append({
                "filename": filename,
                "status": "success",
                # "candidate_id": c_guid
            })

        return jsonify({"results": results}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
