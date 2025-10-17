import os
import smtplib
from dotenv import load_dotenv
from flask import request, jsonify
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database.db_handler import get_db_connection

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


# ---------------------------------------------------
# Helper Function: Send Email to Candidate
# ---------------------------------------------------
def send_review_email(to_email, first_name, selection_status, role):
    try:
        if selection_status not in ["Selected", "Rejected"]:
            return "Invalid selection status. Email not sent."

        subject = f"Application Update - {selection_status}"
            

        if selection_status == "Selected":
            body = f"""
Hi {first_name or ''},

We are pleased to inform you that you have been {selection_status} for the position of {role} at CrewNest.
Our HR team will reach out to you shortly with further details regarding your joining process.

Congratulations, and welcome aboard!

Best regards,  
CrewNest HR Team
"""
        else:
            body = f"""
Hi {first_name or ''},

Thank you for your time and effort throughout the selection process.
After careful consideration, we regret to inform you that you have been {selection_status} for the {role} position.
We sincerely appreciate your interest in joining CrewNest and encourage you to apply for future opportunities with us.

We wish you continued success in your career ahead.

Best regards,  
CrewNest HR Team
"""

        # Create MIME message
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Send email via SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)

        return f"Email sent successfully to {to_email}."

    except Exception as e:
        return f"Error sending email: {e}"


# ---------------------------------------------------
# POST API: submitInterviewInfo
# ---------------------------------------------------
def submit_interview_info():
    try:
        payload = request.get_json(force=True)
        job_id = payload.get('jobId')
        candidate_id = payload.get('candidateId')
        join_status = payload.get('joinStatus')
        feedback = payload.get('feedback')
        selection_status = payload.get('selectionStatus')
        role = payload.get('role')

        if not all([job_id, candidate_id, join_status]):
            return jsonify({
                "isSuccess": False,
                "message": "Missing required fields",
                "statusCode": 400
            }), 400

        selection_status = (selection_status or "").strip()

        score_map = {
            'Selected': 85,
            'Rejected': 25,
            'Under Review': 50
        }

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Step 1: Check if interview info already exists
        check_query = """
            SELECT 1 FROM interviewinfo WHERE JobId = %s AND CandidateId = %s
        """
        cursor.execute(check_query, (job_id, candidate_id))
        exists = cursor.fetchone()

        if exists:
            update_query = """
                UPDATE interviewinfo
                SET JoinStatus = %s,
                    Feedback = %s,
                    SelectionStatus = %s
                WHERE JobId = %s AND CandidateId = %s
            """
            cursor.execute(update_query, (join_status, feedback, selection_status, job_id, candidate_id))
        else:
            insert_query = """
                INSERT INTO interviewinfo 
                (JobId, CandidateId, JoinStatus, Feedback, SelectionStatus)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (job_id, candidate_id, join_status, feedback, selection_status))

        # Step 2: Update jobassessments table if status is valid
        assessment_sqnc = 3
        assessment_name = 'Teams Interview'

        if selection_status in score_map:
            score_value = score_map[selection_status]

            update_assessment = """
                UPDATE jobassessments
                SET status = 'Completed', score = %s
                WHERE jobId = %s
                  AND candidateId = %s
                  AND assessmentSqnc = %s
                  AND assessmentName = %s
            """
            cursor.execute(update_assessment, (score_value, job_id, candidate_id, assessment_sqnc, assessment_name))

            update_application = """
                UPDATE jobapplication
                SET LatestStatus = %s, Score = %s
                WHERE JobId = %s AND CandidateId = %s
            """
            cursor.execute(update_application, (selection_status, score_value, job_id, candidate_id))
        conn.commit()

        # Step 3: Send email to candidate if Selected/Rejected
        email_message = None
        if selection_status in ["Selected", "Rejected"]:
            cursor.execute(
                "SELECT first_name, email FROM candidateprofile WHERE id = %s", (candidate_id,)
            )
            candidate = cursor.fetchone()
            if candidate and candidate.get("email"):
                to_email = candidate["email"]
                first_name = candidate.get("first_name", "")
                email_message = send_review_email(to_email, first_name, selection_status, role)
            else:
                email_message = "Candidate email not found."

        return jsonify({
            "isSuccess": True,
            "message": f"Interview info submitted successfully.",
            "status": "success",
            "statusCode": 200
        })

    except Exception as e:
        return jsonify({
            "isSuccess": False,
            "message": f"Error: {str(e)}",
            "statusCode": 500
        }), 500

    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except:
            pass
