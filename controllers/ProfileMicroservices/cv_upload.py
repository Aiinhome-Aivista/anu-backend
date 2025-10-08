import os
import uuid
import json
import re
from flask import request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import google.generativeai as genai
import fitz  # PyMuPDF for reading PDF content
from database.db_handler import get_db_connection
load_dotenv()


API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)


UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

# ---------- Clean Experience Value ----------
def extract_experience_years(exp_text):
    """
    Extracts realistic experience duration (e.g. '5 years') from text.
    Filters out year-like values (>= 100).
    """
    if not exp_text:
        return ""

    # Find all numbers (like 1, 1.5, 10, 2021)
    matches = re.findall(r"(\d+(\.\d+)?)", exp_text)

    if not matches:
        return exp_text.strip()

    # Convert to float and filter out unrealistic values (e.g., 1900, 2021)
    years = [float(m[0]) for m in matches if 0 < float(m[0]) <= 50]

    if years:
        # Pick the highest realistic experience value
        return f"{int(max(years))} years" if max(years).is_integer() else f"{max(years)} years"

    # If all found numbers were unrealistic (like 2021), return empty
    return ""


# ---------- Main Upload Function (No app dependency) ----------
def upload_cv():
    try:
        # Check if file exists in request
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

        # Save file to uploads folder
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # ---------- Extract Text ----------
        if filename.lower().endswith(".pdf"):
            text_content = extract_text_from_pdf(filepath)
        else:
            text_content = "Non-PDF extraction not implemented"

        if not text_content.strip():
            return jsonify({"message": "Failed to extract data from CV"}), 400

        # ---------- Generate JSON using Gemini ----------
        model = genai.GenerativeModel("gemini-2.5-flash")  
        prompt = f"""
        From the following CV text, extract information in JSON format with these exact keys:
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

        # Ensure all expected keys exist
        expected_keys = [
            "title", "first_name", "middle_name", "last_name", "email",
            "contact", "address", "latestrole", "education", "designation",
            "certification", "skills", "experience"
        ]
        for key in expected_keys:
            extracted_data.setdefault(key, "")

        # Standardize experience field
        extracted_data["experience"] = extract_experience_years(extracted_data.get("experience", ""))

        # Generate unique candidate ID
        c_guid = str(uuid.uuid4())

        # ---------- Insert into Database ----------
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
        cursor.close()
        conn.close()

        return jsonify({
            "message": "CV uploaded successfully"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
