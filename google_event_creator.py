from __future__ import print_function
import os
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Change scope from read-only → full calendar access
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_service():
    """Authenticate and return a Google Calendar service client."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

def create_event(service, event_data):
    """Create a calendar event from given JSON data with sensible defaults."""
    # Defaults for missing fields
    summary = event_data.get("summary", "Untitled Event")
    description = event_data.get("description", "No description provided.")
    timezone = event_data.get("timezone", "America/Los_Angeles")

    # Handle date/time with fallback to "today + 1 hour"
    start_str = event_data.get("start")
    end_str = event_data.get("end")

    if not start_str:
        now = datetime.now()
        start_time = now + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
    else:
        start_time = datetime.fromisoformat(start_str)
        if end_str:
            end_time = datetime.fromisoformat(end_str)
        else:
            end_time = start_time + timedelta(hours=1)

    event_body = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_time.isoformat(), 'timeZone': timezone},
        'end': {'dateTime': end_time.isoformat(), 'timeZone': timezone},
    }

    event = service.events().insert(calendarId='primary', body=event_body).execute()
    print(f"✅ Created: {event.get('summary')} — {event.get('htmlLink')}")
    return event

def create_events_from_json(file_path):
    """Load events from JSON and create each one in Google Calendar."""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        events = json.load(f)

    if not isinstance(events, list):
        print("❌ JSON must be a list of event objects.")
        return

    service = get_service()

    for i, ev in enumerate(events, start=1):
        print(f"\n📅 Creating event {i}/{len(events)}:")
        try:
            create_event(service, ev)
        except Exception as e:
            print(f"⚠️ Failed to create event {i}: {e}")

def main():
    file_path = "events.json"
    create_events_from_json(file_path)

if __name__ == "__main__":
    main()
