import os
import smtplib
from datetime import datetime
from email.header import Header
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from email.mime.multipart import MIMEMultipart
from database.db_handler import get_db_connection
from utils.google_meet import create_google_meet_link


# ---------- Email Configuration ----------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def book_candidate_slot():
    try:
        data = request.get_json()
        candidate_id = data.get("candidateId")  
        job_id = data.get("jobid")
        selected_slot = data.get("selectedslot", {})

        slot_id = selected_slot.get("id")
        date = selected_slot.get("date")
        time_slot = selected_slot.get("timeSlot")
        start_time = selected_slot.get("startTime")
        end_time = selected_slot.get("endTime")

        if not all([candidate_id, job_id, slot_id]):
            return jsonify({
                "isSuccess": False,
                "message": "Missing required fields: candidateId, jobid, or selectedslot.id",
                "status": "error",
                "statusCode": 400
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Step 1️: Get candidate details from candidateprofile using numeric ID
        cursor.execute("""
            SELECT id, first_name, last_name, email 
            FROM candidateprofile 
            WHERE id = %s
        """, (candidate_id,))
        candidate_row = cursor.fetchone()
        if not candidate_row:
            return jsonify({
                "isSuccess": False,
                "message": f"No candidate found with ID {candidate_id}",
                "status": "error",
                "statusCode": 404
            }), 404

        numeric_candidate_id = candidate_row["id"]
        candidate_email = candidate_row["email"]
        candidate_name = f"{candidate_row['first_name']} {candidate_row['last_name']}".strip()
        candidate_first_name = candidate_row["first_name"]

        # Step 2️: Get hiring manager ID from job table
        cursor.execute("SELECT hiringManagerId, role FROM job WHERE id = %s", (job_id,))
        job_row = cursor.fetchone()
        if not job_row:
            return jsonify({
                "isSuccess": False,
                "message": f"No hiring manager found for job ID {job_id}",
                "status": "error",
                "statusCode": 404
            }), 404

        hiring_manager_id = job_row["hiringManagerId"]
        job_role = job_row["role"]

        # Step 3️: Update slot as booked (store candidate email for clarity)
        cursor.execute("""
            UPDATE hiringManagerSelectedSlots
            SET isBooked = 1,
                candidateId = %s,
                jobid= %s,
                updatedOn = NOW()
            WHERE id = %s
        """, (candidate_id, job_id, slot_id))

        # Step 4️: Update jobassessments table
        cursor.execute("""
            UPDATE jobassessments
            SET status = 'Interview Scheduled'
            WHERE jobId = %s
              AND candidateId = %s
              AND assessmentName = 'Teams Interview'
        """, (job_id, numeric_candidate_id))

        # Step 5️: Update jobapplication table
        cursor.execute("""
            UPDATE jobapplication
            SET LatestStatus = 'Interview Scheduled'
            WHERE JobId = %s
              AND CandidateId = %s
              AND LatestStatus = 'Interview Schedule Pending'
        """, (job_id, numeric_candidate_id))

        conn.commit()

        # Step 6️: Send emails
        send_interview_emails(
            candidate_email=candidate_email,
            candidate_name=candidate_name,
            candidate_first_name=candidate_first_name,
            manager_email=hiring_manager_id,
            job_id=job_id,
            job_role=job_role,
            date=date,
            time_slot=time_slot,
            start_time=start_time,
            end_time=end_time
        )

        cursor.close()
        conn.close()

        return jsonify({
            "isSuccess": True,
            "message": f"Slot booked successfully for candidate ID {candidate_id}.",
            "status": "success",
            "statusCode": 200
        }), 200

    except Exception as e:
        return jsonify({
            "isSuccess": False,
            "message": str(e),
            "status": "error",
            "statusCode": 500
        }), 500


def send_interview_emails(candidate_email, candidate_first_name, candidate_name, manager_email, job_id, job_role, date, time_slot, start_time, end_time):
    """Send two different CrewNest-branded HTML emails to candidate and hiring manager."""
    
        # Dynamically generate meet link with manager as host
    start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
    end_dt = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")

    meet_link = create_google_meet_link(
    summary=f"Interview for {job_role}",
    description=f"Interview with {candidate_name}",
    start_time=start_dt.isoformat(),
    end_time=end_dt.isoformat()
    )

    if not meet_link :
        meet_link = "https://meet.google.com/"  # fallback in case of API error

    # ---------- Candidate Email ----------
    candidate_subject = f"Interview Scheduled for {job_role} – on {date}"
    candidate_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #DFB916;">CrewNest Interview Confirmation</h2>
        <p>Dear {candidate_first_name},</p>
        <p>We’re happy to inform you that your interview for <strong>{job_role}</strong> has been successfully scheduled.</p>
        <p><strong>Interview Details:</strong></p>
        <ul>
            <li><strong>Date:</strong> {date}</li>
            <li><strong>Time Slot:</strong> {time_slot}</li>
            <li><strong>Meeting Link:</strong> <a href="{meet_link}" target="_blank">{meet_link}</a></li>
        </ul>
        <p>Please ensure you join the meeting 5 minutes before the start time.</p>
        <p>We wish you all the best for your interview!</p>
        <br>
        <p>Regards,<br><strong>The CrewNest Team</strong></p>
        <hr>
        <footer style="font-size:12px;color:#777;">This is an automated message from CrewNest. Please do not reply.</footer>
    </body>
    </html>
    """

    # ---------- Hiring Manager Email ----------
    manager_subject = f"Interview Scheduled for {job_role} – on {date}"
    manager_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #DFB916;">CrewNest Interview Notification</h2>
        <p>Dear Hiring Manager,</p>
        <p>An interview has been successfully scheduled for <strong>{job_role}</strong> with the following details:</p>
        <ul>
            <li><strong>Candidate Name:</strong> {candidate_name}</li>
            <li><strong>Date:</strong> {date}</li>
            <li><strong>Time Slot:</strong> {time_slot}</li>
            <li><strong>Meeting Link:</strong> <a href="{meet_link}" target="_blank">{meet_link}</a></li>
        </ul>
        <p>Please ensure your availability during this time slot.</p>
        <p>Best regards,<br><strong>CrewNest Interview Coordination Team</strong></p>
        <hr>
        <footer style="font-size:12px;color:#777;">This notification was generated by CrewNest Interview Management System.</footer>
    </body>
    </html>
    """

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

            # Send to candidate
            msg_c = MIMEMultipart()
            msg_c["From"] = EMAIL_ADDRESS
            msg_c["To"] = candidate_email
            # msg_c["Subject"] = candidate_subject
            msg_c["Subject"] = str(Header(candidate_subject, 'utf-8'))
            msg_c.attach(MIMEText(candidate_body, "html", _charset="utf-8"))
            server.send_message(msg_c)

            # Send to hiring manager
            msg_m = MIMEMultipart()
            msg_m["From"] = EMAIL_ADDRESS
            msg_m["To"] = manager_email
            # msg_m["Subject"] = manager_subject
            msg_m["Subject"] = str(Header(manager_subject, 'utf-8'))
            msg_m.attach(MIMEText(manager_body, "html", _charset="utf-8"))
            server.send_message(msg_m)

            print("Emails sent to:", candidate_email, "and", manager_email)

    except Exception as e:
        print("Email send error:", str(e))
