# pyrefly: ignore [missing-import]
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def generate_token():
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)
    with open("token.pkl", "wb") as token_file:
        pickle.dump(creds, token_file)
    print("✅ Google Calendar access token created and saved as token.pkl")

if __name__ == "__main__":
    generate_token()
