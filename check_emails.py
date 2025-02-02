import os
import base64
import re
import requests
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Flask API URL (Update this with your actual Flask API endpoint)
FLASK_API_URL = "http://127.0.0.1:5000/update_seats"

def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

def check_unstop_emails():
    """Fetch latest emails from Unstop and update seat count."""
    service = get_gmail_service()
    results = service.users().messages().list(userId='me', q="from:noreply@emails.unstop.com").execute()
    
    if 'messages' in results:
        for msg in results['messages']:
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            payload = msg_data['payload']
            
            for part in payload.get('parts', []):
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    if "Successfully registered" in body:
                        print("New registration detected! Updating available seats.")
                        update_seat_count()
                        return

def update_seat_count():
    """Call Flask API to reduce seat count."""
    response = requests.post(FLASK_API_URL, json={"action": "decrease"})
    if response.status_code == 200:
        print("Seat count updated successfully!")
    else:
        print("Error updating seat count:", response.text)

if __name__ == "__main__":
    check_unstop_emails()
