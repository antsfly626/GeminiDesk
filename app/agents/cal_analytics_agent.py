import os
import json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import google.generativeai as genai

# ========== CONFIG ==========
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# ========== AUTH & SERVICE SETUP ==========
def get_calendar_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=8080)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)

# ========== FETCH EVENTS ==========
def get_past_week_events(service):
    now = datetime.utcnow()
    one_week_ago = now - timedelta(days=7)
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=one_week_ago.isoformat() + "Z",
            timeMax=now.isoformat() + "Z",
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return events_result.get("items", [])

# ========== ANALYTICS CHARTS ==========
def generate_charts(events):
    if not events:
        print("No events found for the past week.")
        return None, None, {}

    # Use summary as label; group by title
    event_counts = Counter([e.get("summary", "Untitled") for e in events])

    # Duration analytics (if times available)
    durations = defaultdict(float)
    for e in events:
        start = e["start"].get("dateTime")
        end = e["end"].get("dateTime")
        title = e.get("summary", "Untitled")
        if start and end:
            s, e_ = datetime.fromisoformat(start[:-1]), datetime.fromisoformat(end[:-1])
            durations[title] += (e_ - s).total_seconds() / 3600  # hours
        else:
            durations[title] += 1  # assume 1 hour default

    # --- PIE CHART: time spent per event ---
    pie_labels, pie_values = zip(*durations.items())
    plt.figure(figsize=(6, 6))
    plt.pie(pie_values, labels=pie_labels, autopct="%1.1f%%", startangle=140)
    plt.title("Time Spent per Event (Past 7 Days)")
    pie_path = "weekly_pie_chart.png"
    plt.savefig(pie_path, bbox_inches="tight")
    plt.close()

    # --- BAR CHART: events per day ---
    days = [datetime.fromisoformat(e["start"].get("dateTime", datetime.utcnow().isoformat())).strftime("%a") for e in events]
    bar_counts = Counter(days)
    plt.figure(figsize=(7, 4))
    plt.bar(bar_counts.keys(), bar_counts.values())
    plt.title("Number of Events per Day")
    plt.xlabel("Day")
    plt.ylabel("Events")
    bar_path = "weekly_bar_chart.png"
    plt.savefig(bar_path, bbox_inches="tight")
    plt.close()

    return pie_path, bar_path, {"durations": durations, "counts": bar_counts}

# ========== GEMINI SUMMARIES ==========
def generate_descriptions(data):
    model = genai.GenerativeModel("models/gemini-2.0-pro")
    pie_prompt = f"Describe what this pie chart shows in 2 sentences. Data: {list(data['durations'].items())}"
    bar_prompt = f"Summarize the bar chart data in 2 sentences. Data: {list(data['counts'].items())}"
    week_prompt = "Give an overall 3-sentence weekly productivity summary based on these datasets."

    pie_desc = model.generate_content(pie_prompt).text
    bar_desc = model.generate_content(bar_prompt).text
    week_desc = model.generate_content(week_prompt).text
    return pie_desc, bar_desc, week_desc

# ========== MAIN FUNCTION ==========
def main():
    service = get_calendar_service()
    events = get_past_week_events(service)

    pie_path, bar_path, data = generate_charts(events)
    if not data:
        return

    pie_desc, bar_desc, week_desc = generate_descriptions(data)

    # Save JSON summary
    result = {
        "pie_chart": pie_path,
        "bar_chart": bar_path,
        "pie_chart_description": pie_desc,
        "bar_chart_description": bar_desc,
        "weekly_summary": week_desc,
    }

    with open("weekly_report.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)

    print("\n✅ Weekly analytics generated:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
