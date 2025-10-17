import os
import pickle
from datetime import datetime
from googleapiclient.discovery import build

def create_google_meet_link(summary, description, start_time, end_time):
    """
    Creates a Google Meet link using HR Gmail's Google Calendar API.
    """

    try:
        # Load stored credentials
        if not os.path.exists("token.pkl"):
            raise FileNotFoundError("token.pkl not found. Run generate_token.py first.")

        with open("token.pkl", "rb") as token_file:
            creds = pickle.load(token_file)

        # Build Calendar API service
        service = build("calendar", "v3", credentials=creds)

        # Create Google Calendar event with Meet link
        event = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_time, "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_time, "timeZone": "Asia/Kolkata"},
            "conferenceData": {
                "createRequest": {
                    "requestId": f"meet-{datetime.now().timestamp()}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
        }

        created_event = (
            service.events()
            .insert(calendarId="primary", body=event, conferenceDataVersion=1)
            .execute()
        )

        meet_link = created_event["conferenceData"]["entryPoints"][0]["uri"]
        print(f"Google Meet created: {meet_link}")
        return meet_link

    except Exception as e:
        print("Error creating Google Meet:", str(e))
        return None
