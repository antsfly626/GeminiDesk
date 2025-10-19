from __future__ import print_function
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Scopes define the level of access requested
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def main():
    creds = None
    # Load previously saved tokens, if available
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no valid credentials, trigger login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Create OAuth flow from your credentials file
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            # Run the local server for authorization
            creds = flow.run_local_server(port=8080)
        # Save access/refresh tokens for future runs
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Build the Calendar service
    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    print('Getting the next 10 upcoming events:')
    events_result = (
        service.events()
        .list(calendarId='primary', maxResults=10, singleEvents=True, orderBy='startTime')
        .execute()
    )
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
        return

    # Print event details
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"{start} — {event.get('summary', 'No title')}")

if __name__ == '__main__':
    main()
