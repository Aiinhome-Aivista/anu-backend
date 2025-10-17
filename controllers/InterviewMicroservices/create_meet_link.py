# create_meet_link.py
import uuid
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Google API configuration
GOOGLE_CREDENTIALS_FILE = r"D:\ANU_backend_2025\anu-backend\controllers\InterviewMicroservices\credentials.json"  

GOOGLE_CALENDAR_ID = "primary"
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def create_meet_link(manager_email, job_role, date, start_time, end_time):
    """
    Creates a Google Meet link and assigns the hiring manager as host.
    If Google API fails, falls back to a dummy meet-like link.
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_FILE, scopes=SCOPES
        )
        delegated_credentials = credentials.with_subject(manager_email)
        service = build("calendar", "v3", credentials=delegated_credentials)

        event = {
            "summary": f"Interview for {job_role}",
            "description": "CrewNest Interview Meeting",
            "start": {
                "dateTime": f"{date}T{start_time}:00",
                "timeZone": "Asia/Kolkata"
            },
            "end": {
                "dateTime": f"{date}T{end_time}:00",
                "timeZone": "Asia/Kolkata"
            },
            "conferenceData": {
                "createRequest": {
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                    "requestId": str(uuid.uuid4())
                }
            },
            "attendees": [{"email": manager_email}],
        }

        created_event = service.events().insert(
            calendarId=GOOGLE_CALENDAR_ID,
            body=event,
            conferenceDataVersion=1
        ).execute()

        meet_link = created_event["conferenceData"]["entryPoints"][0]["uri"]
        print(f"Google Meet created for {manager_email}: {meet_link}")
        return meet_link

    except Exception as e:
        print(" Failed to create Google Meet link:", e)
        # Fallback dummy link for testing
        dummy_link = f"https://meet.google.com/{uuid.uuid4().hex[:3]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:3]}"
        print(f"Using fallback dummy meet link: {dummy_link}")
        return dummy_link
