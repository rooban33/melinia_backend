from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
import time
import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Event details
events = {
    "hackathon": {
        "email": "meliniahackathon25@gmail.com",
        "seats": 50,
        "last_checked": 0
    },
    "ideathon": {
        "email": "meliniathepitchpit@gmail.com",
        "seats": 50,
        "last_checked": 0
    }
}

# Function to authenticate and return Gmail service
def get_gmail_service(event_name):
    creds = None
    credentials_file = f'credentials_{event_name}.json'  # Use different credentials files
    token_file = f'token_{event_name}.json'  # Unique token file per event

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

# Function to check emails and update seat count
def check_unstop_emails(event_name):
    global events
    current_time = time.time()
    
    # Return previous value if last check was within 5 minutes
    if current_time - events[event_name]['last_checked'] < 300:
        return events[event_name]['seats']
    
    service = get_gmail_service(event_name)
    results = service.users().messages().list(userId='me', q="from:noreply@emails.unstop.com").execute()
    
    if 'messages' in results:
        for msg in results['messages']:
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            payload = msg_data['payload']
            
            for part in payload.get('parts', []):
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    if "Successfully registered" in body:
                        events[event_name]['seats'] -= 1 if events[event_name]['seats'] > 0 else 0
                        events[event_name]['last_checked'] = current_time
                        break
    return events[event_name]['seats']

@app.route('/available_seats/<event_name>', methods=['GET'])
def get_available_seats(event_name):
    if event_name not in events:
        return jsonify({"error": "Invalid event name"}), 400
    seats = check_unstop_emails(event_name)
    return jsonify({"event": event_name, "available_seats": seats})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
