from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
# Run once to initialize the flow (no need to actually complete auth)
flow.redirect_uri = 'http://127.0.0.1:8080/'  # This is what run_local_server sets internally
print("👉 Redirect URI you must whitelist:", flow.redirect_uri)
