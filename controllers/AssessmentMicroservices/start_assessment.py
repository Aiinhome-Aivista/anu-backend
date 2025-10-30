import os
import json
import uuid
import base64
import asyncio
import requests
import tempfile
import edge_tts  
import subprocess
from dotenv import load_dotenv
import speech_recognition as sr
from pymediainfo import MediaInfo
from datetime import datetime, timedelta
from flask import request, jsonify, current_app
from database.db_handler import get_db_connection

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_API_URL = os.getenv("MISTRAL_API_URL")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL")

BASE_URL = os.getenv("BASE_URL")

# -----------------------------
# Dynamic Executable Paths
# -----------------------------
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Project root is two levels up
# PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

# APPS_DIR = os.path.join(PROJECT_ROOT, "apps")

# FFMPEG_PATH = os.path.join(APPS_DIR, "ffmpeg.exe")
# FFPROBE_PATH = os.path.join(APPS_DIR, "ffprobe.exe")
# RHUBARB_PATH = os.path.join(APPS_DIR, "rhubarb.exe")

# Generate Edge-tts-audio
async def generate_neural_audio(text, output_path):
    """Generate high-quality neural TTS using en-US-JennyNeural voice."""
    voice = "en-IN-PrabhatNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

# Generate Rhubarb-json
# def generate_lipsync_json(audio_filename, text, session_id, unique_id):
#     try:
#         # Define paths
#         static_lipsync_dir = os.path.join("static", "lipsync")
#         os.makedirs(static_lipsync_dir, exist_ok=True)

#         json_output = os.path.join(static_lipsync_dir, f"response_{session_id}_{unique_id}_lipsync.json")

#         # Create dialog text file
#         dialog_file = f"static/audio/dialog_{session_id}_{unique_id}.txt"
#         with open(dialog_file, "w", encoding="utf-8") as f:
#             f.write(text)

#         # Use absolute path (safe for all environments)
#         rhubarb_path = os.path.abspath(RHUBARB_PATH)

#         #print(f"Running Rhubarb from: {rhubarb_path}")  

#         if not os.path.exists(rhubarb_path):
#             raise FileNotFoundError(f"Rhubarb executable not found at {rhubarb_path}")

#         # Convert mp3 to ogg (Rhubarb prefers wav/ogg)
#         ogg_filename = audio_filename.replace(".mp3", ".ogg")
#         subprocess.run(
#             [FFMPEG_PATH, "-y", "-i", audio_filename, ogg_filename],
#             stdout=subprocess.DEVNULL,
#             stderr=subprocess.DEVNULL,
#             check=True
#         )


#         # Run Rhubarb
#         result = subprocess.run([
#             rhubarb_path,
#             ogg_filename,
#             "-o", json_output,
#             "-d", dialog_file,
#             "-f", "json"
#         ], capture_output=True, text=True)

#         if result.returncode != 0:
#             #print(" Rhubarb Error:", result.stderr)
#             raise RuntimeError(f"Rhubarb failed: {result.stderr}")

#         # Get audio duration
#         info = MediaInfo.parse(ogg_filename)
#         duration = float(info.tracks[0].duration) / 1000 if info.tracks[0].duration else 0.0

#         # Append metadata
#         with open(json_output, "r+", encoding="utf-8") as f:
#             data = json.load(f)
#             data["metadata"] = {
#                 "soundFile": ogg_filename,
#                 "duration": round(duration, 2)
#             }
#             f.seek(0)
#             json.dump(data, f, indent=2)
#             f.truncate()

#         os.remove(dialog_file)
#         return json_output, data  

#     except Exception as e:
#         #print("Rhubarb generation failed:", e)
#         return None, {}

# AI Screening
def start_assessment():
    conn = None
    cursor = None
    SESSION_DURATION_MINUTES = 3
    remaining_time_str = f"{SESSION_DURATION_MINUTES:02d}:00"

    try:
        # -----------------------------
        # Parse request
        # -----------------------------
        if request.content_type and request.content_type.startswith("multipart/form-data"):
            candidate_id = request.form.get("candidateId")
            job_id = request.form.get("jobId")
            session_id = request.form.get("sessionId")  
            last_answer = ""

            if "audio" in request.files:
                audio_file = request.files["audio"]
                recognizer = sr.Recognizer()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                    audio_file.save(temp_audio.name)
                    with sr.AudioFile(temp_audio.name) as source:
                        audio_data = recognizer.record(source)
                        last_answer = recognizer.recognize_google(audio_data)
        else:
            data = request.get_json()
            candidate_id = data.get("candidateId")
            job_id = data.get("jobId")
            session_id = data.get("sessionId")
            last_answer = data.get("answer", "").strip()

        if not candidate_id or not job_id:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "Invalid input. Required: candidateId, jobId.",
                "isSuccess": False
            }), 400

        # -----------------------------
        # Fetch candidate info
        # -----------------------------
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM candidateprofile WHERE id = %s", (candidate_id,))
        candidate = cursor.fetchone()

        if not candidate:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": "Candidate not found.",
                "isSuccess": False
            }), 404

        # candidate_name = f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}".strip()
        candidate_name = candidate.get('first_name')
        skills = candidate.get('skills', '')
        education = candidate.get('education', '')
        experience = candidate.get('experience', '')
        latestrole = candidate.get('latestrole','')
        address =  candidate.get('address','')
        # -----------------------------
        # Handle Session
        # -----------------------------
        now = datetime.now()
        session_valid = False
        if session_id:
            cursor.execute("""
                SELECT * FROM assessment_session_log
                WHERE session_id = %s AND candidate_id = %s AND job_id = %s
                ORDER BY created_at DESC LIMIT 1
            """, (session_id, candidate_id, job_id))
            session_row = cursor.fetchone()
            # if session_row:
            #     created_at = session_row["created_at"]
            #     if now - created_at <= timedelta(minutes=10):
            #         session_valid = True  
            #     else:
            #         session_valid = False
            if session_row:
                created_at = session_row["created_at"]
                elapsed = now - created_at
                total_duration = timedelta(minutes=SESSION_DURATION_MINUTES)
                remaining = total_duration - elapsed
                remaining_seconds = max(0, int(remaining.total_seconds()))
                minutes, seconds = divmod(remaining_seconds, 60)
                remaining_time_str = f"{minutes:02d}:{seconds:02d}"

                if elapsed <= total_duration:
                    session_valid = True
                else:
                    session_valid = False
            else:
                remaining_time_str = f"{SESSION_DURATION_MINUTES:02d}:00"

        if session_id and not session_valid:
            # Session expired
            return jsonify({
                "status": "failed",
                "statusCode": 440,
                "message": f"Hi {candidate_name}, your interview has ended. Thank you for taking the time to speak with us. Wishing you all the best for your future!",
                "isSuccess": False
            }), 440


        # -----------------------------
        # Build dynamic prompt
        # -----------------------------
        if last_answer == "":
            prompt = f"""
        You are a friendly HR interviewer conducting a structured job interview.

        Candidate Info:
        Name: {candidate_name}
        Education: {education}
        Experience: {experience}
        Skills: {skills}

        --- INSTRUCTIONS ---
        # 1. Greet the candidate naturally (e.g.,"Hi, I’m Subho, from your recruitment team — nice to meet you! {candidate_name}").
        # 2. Then ask **exactly ONE question** about their education, in **1-2 short sentences only**.
        # 3. **Do not** add explanations, comments, examples, or multiple questions.
        # 4. **Output only the question text** — no other sentences or instructions.
        # 5. Keep tone friendly, professional, and conversational.
        1. Greet the candidate naturally (e.g., "Hi, I’m Subho, from your recruitment team — nice to meet you, {candidate_name}!").
        2. Then ask **exactly ONE question** about their education background — such as what they studied, their college experience, or subjects they enjoyed.
        3. **Do NOT mention or refer to any grades, marks, percentages, CGPA, GPA, or scores — focus only on their learning, projects, or experiences.**
        4. **Do not** add explanations, comments, examples, or multiple questions.
        5. **Output only the question text** — nothing else.
        6. Keep the tone friendly, professional, and conversational.
        7. **Do not** add explanations, comments, examples, or multiple questions.
        8. **Do not** use abbreviations or expansions in parentheses.
        9. When discussing technologies, focus on types or roles, not specific names.
        """
        else:
            prompt = f"""
        You are a friendly HR interviewer continuing a structured job interview.

        Candidate Info:
        Name: {candidate_name}
        Education: {education}
        Experience: {experience}
        Skills: {skills}

        The candidate just answered: "{last_answer}"

        --- INSTRUCTIONS ---
        # 1. Ask **exactly ONE short question** (1-2 sentences) based on the candidate’s previous answer.
        # 2. Follow this sequence: Education → Experience → Skills → Technical → Hobbies/Personality.
        # 3. **Do not** include follow-up questions, examples, or explanations.
        # 4. **Output only the next question** — nothing else.
        # 5. Keep tone friendly, professional, and conversational.
        1. Ask **exactly ONE short question** (1–2 sentences) based on the candidate’s previous answer.
        2. Follow this sequence: Education → Experience → Skills → Technical → Hobbies/Personality.
        3. **Do NOT mention or refer to any grades, marks, percentages, CGPA, GPA, or scores — focus on ideas, experiences, or skills.**
        4. **Do not** include follow-up questions, examples, or explanations.
        5. **Output only the next question** — nothing else.
        6. Keep tone friendly, professional, and conversational.
        7. **Do not** add explanations, comments, examples, or multiple questions.
        8. **Do not** use abbreviations or expansions in parentheses.
        9. When discussing technologies, focus on types or roles, not specific names.

        """

        # -----------------------------
        # Call Mistral API
        # -----------------------------
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MISTRAL_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }

        response = requests.post(MISTRAL_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        question_text = None
        if "choices" in result and len(result["choices"]) > 0:
            question_text = result["choices"][0]["message"]["content"].strip()
        elif "output" in result:
            question_text = result["output"].strip()

        if not question_text:
            return jsonify({
                "status": "failed",
                "statusCode": 502,
                "message": "Model did not return a valid question.",
                "isSuccess": False
            }), 502

        # -----------------------------
        # Generate Neural Audio
        # -----------------------------
        audio_dir = os.path.join(current_app.root_path, "static", "audio")
        os.makedirs(audio_dir, exist_ok=True)
        audio_filename = f"question_{candidate_id}_{job_id}_{os.getpid()}.mp3"
        audio_path = os.path.join(audio_dir, audio_filename)
        asyncio.run(generate_neural_audio(question_text, audio_path))
        audio_url = f"{BASE_URL}/static/audio/{audio_filename}"

        # -----------------------------
        # Generate Rhubarb JSON
        # -----------------------------
        # unique_id = uuid.uuid4().hex[:6]
        # lipsync_path, rhubarb_json = generate_lipsync_json(audio_path, question_text, session_id, unique_id)
        # lipsync_url = f"{BASE_URL}/static/lipsync/{os.path.basename(lipsync_path)}" if lipsync_path else None


        # -----------------------------
        # Save session log in DB
        # -----------------------------
        qa_pair = {"question": question_text, "answer": last_answer}

        if session_valid:
            existing_log = json.loads(session_row["question_answer"])

            #  Step 1: Fill last unanswered question
            if last_answer and existing_log and existing_log[-1].get("answer", "") == "":
                existing_log[-1]["answer"] = last_answer
            elif last_answer:
                # If something went out of order
                existing_log.append({"questionNo": len(existing_log) + 1, "question": "", "answer": last_answer})

            #  Step 2: Append new question
            existing_log.append({
                "questionNo": len(existing_log) + 1,
                "question": question_text,
                "answer": ""
            })

            created_at = session_row["created_at"]
            current_status = session_row["status"]

            #  Step 3: Keep your old DB update logic (same as before)
            if current_status == "active" and datetime.now() - created_at > timedelta(minutes=3):
                cursor.execute("""
                    UPDATE assessment_session_log
                    SET question_answer = %s, status = %s
                    WHERE id = %s
                """, (json.dumps(existing_log), "completed", session_row["id"]))
            else:
                cursor.execute("""
                    UPDATE assessment_session_log
                    SET question_answer = %s
                    WHERE id = %s
                """, (json.dumps(existing_log), session_row["id"]))

            conn.commit()

        else:
            # New session — same as before
            session_id = str(uuid.uuid4())
            qa_list = [{
                "questionNo": 1,
                "question": question_text,
                "answer": ""
            }]
            cursor.execute("""
                INSERT INTO assessment_session_log (candidate_id, job_id, session_id, question_answer, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (candidate_id, job_id, session_id, json.dumps(qa_list), 'active'))
            conn.commit()



        # -----------------------------
        # Success response
        # -----------------------------
        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": "Assessment question generated successfully.",
            "isSuccess": True,
            "result": {
                "candidateId": candidate_id,
                "jobId": job_id,
                "sessionId": session_id,
                "question": question_text,
                "audioUrl": audio_url,
                #"lipsyncUrl": lipsync_url,
                "remainingTime": remaining_time_str
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "failed",
            "statusCode": 500,
            "message": str(e),
            "isSuccess": False
        }), 500

    finally:
        try:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()
        except:
            pass
