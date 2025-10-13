import os
import re
import uuid
import fitz  
import json
import smtplib
from dotenv import load_dotenv
from flask import request, jsonify
import google.generativeai as genai
from email.mime.text import MIMEText
from werkzeug.utils import secure_filename
from email.mime.multipart import MIMEMultipart
from database.db_handler import get_db_connection

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- Email Configuration ----------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


# ---------- Allowed File Extensions ----------
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------- Extract Text from PDF ----------
def extract_text_from_pdf(filepath):
    text = ""
    with fitz.open(filepath) as pdf:
        for page in pdf:
            text += page.get_text()
    return text


# ---------- Send Email Function ----------
def send_confirmation_email(to_email, first_name):
    try:
        subject = "Your CV Submission to CrewNest"
        body = f"""
Hi {first_name if first_name else ''},

Thank you for applying to CrewNest.
Your CV has been successfully submitted.

Username: {to_email} (use this email to log in)

Our recruitment team will review your profile, and we’ll get back to you soon if your application matches our requirements.

Best regards,  
CrewNest HR Team
"""

        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False


# ---------- Main Upload Function ----------
def upload_cv():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']
        email = request.form.get('email')

        if not file or file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if not email:
            return jsonify({"error": "Email is required"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        if filename.lower().endswith(".pdf"):
            text_content = extract_text_from_pdf(filepath)
        else:
            text_content = "Non-PDF extraction not implemented"

        if not text_content.strip():
            return jsonify({"message": "Failed to extract data from CV"}), 400

        model = genai.GenerativeModel("gemini-2.5-flash")  
        prompt = f"""
        You are a CV parsing assistant. 
        Analyze the following resume text and extract the information in a **clean JSON format**,
        where every field value must be a simple string (not a list or object).
        Use these exact keys:
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
            4. 4. For "skills":
                - Extract only *technical skills* mentioned in the CV.
                - These can appear under headings such as: Skills, Technical Skills, Core Competencies, Key Expertise, Technical Proficiency, or similar.
                - Include items like programming languages, frameworks, tools, libraries, databases, cloud platforms, or software.
                - Exclude non-technical items such as spoken or written languages (e.g., English, Hindi, Bengali, etc.).
                - Clean and join all valid skills into a *comma-separated string*, e.g.:
                  "Azure Data Factory, Azure SQL, Node JS, PHP, JavaScript, Angular, React JS, MS SQL, MySQL, SSMS"
            5. Ensure JSON is valid and machine-readable.
        CV Text:
        {text_content}
        """

        response = model.generate_content(prompt)
        raw_text = response.text.strip() if response else "{}"

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
            value = extracted_data.get(key, "")

            if isinstance(value, (list, dict)):
                extracted_data[key] = json.dumps(value, ensure_ascii=False)
            elif value is None:
                extracted_data[key] = ""
            else :
                extracted_data[key] = str(value)
        # ---------- Cleanup: remove non-technical languages from 'skills' ----------
        if "skills" in extracted_data:
            skills_text = extracted_data["skills"]
            non_technical_langs = [
                "english", "hindi", "bengali", "french", "spanish", "german",
                "tamil", "telugu", "marathi", "gujarati", "urdu", "punjabi"
            ]
            cleaned = []
            for skill in [s.strip() for s in skills_text.split(",")]:
                if not any(lang in skill.lower() for lang in non_technical_langs):
                    cleaned.append(skill)
            extracted_data["skills"] = ", ".join(cleaned)

        c_guid = str(uuid.uuid4())

        conn = get_db_connection()
        cursor = conn.cursor()

        # ---------- Email duplication validation ----------
        cursor.execute("SELECT Id FROM applicationuser WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            cursor.close()
            conn.close()
            return jsonify({
                "error": "User already exists."
            }), 400

        if filename.lower().endswith(".pdf"):
            text_content = extract_text_from_pdf(filepath)

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
            extracted_data["email"] or email,
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

        email_to_insert = extracted_data["email"] or email
        cursor.execute(
            "SELECT Id FROM applicationuser WHERE email = %s",
            (email_to_insert,)
        )
        existing = cursor.fetchone()
        
        if not existing:
            cursor.execute(
                "INSERT INTO applicationuser (email, IsHiringManager) VALUES (%s, %s)",
                (email_to_insert, '0')
            )
            conn.commit()

        cursor.close()
        conn.close()

        # ---------- Send Confirmation Email ----------
        send_confirmation_email(email_to_insert, extracted_data["first_name"])

        return jsonify({
            "message": "CV uploaded successfully and confirmation email sent."
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
