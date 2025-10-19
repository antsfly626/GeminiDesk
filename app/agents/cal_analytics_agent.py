import os, json
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import google.generativeai as genai
from notion_client import Client
from dotenv import load_dotenv

# ========= CONFIG =========
load_dotenv()
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
notion = Client(auth=os.getenv("NOTION_TOKEN"))

# ========= AUTH =========
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

# ========= CALENDAR DATA =========
def get_past_week_events(service):
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    res = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=week_ago.isoformat() + "Z",
            timeMax=now.isoformat() + "Z",
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return res.get("items", [])

# ========= DATA AGGREGATION =========
def summarize_events(events):
    durations = defaultdict(float)
    daily_counts = Counter()
    for e in events:
        title = e.get("summary", "Untitled")
        start, end = e["start"].get("dateTime"), e["end"].get("dateTime")
        if start and end:
            s, t = datetime.fromisoformat(start[:-1]), datetime.fromisoformat(end[:-1])
            durations[title] += (t - s).total_seconds() / 3600
            daily_counts[s.strftime("%a")] += 1
        else:
            durations[title] += 1
    return {"durations": durations, "counts": daily_counts}

# ========= IMAGE GENERATION =========
def generate_visuals(data):
    model = genai.GenerativeModel("models/gemini-2.0-pro-vision")
    duration_text = ", ".join(f"{k}: {v:.1f}h" for k, v in data["durations"].items())
    counts_text = ", ".join(f"{k}: {v}" for k, v in data["counts"].items())

    # 1️⃣ dashboard summary card
    dashboard_prompt = (
        f"Create a clean modern dashboard-style image summarizing weekly productivity. "
        f"Show categories with hours worked ({duration_text}) and events per day ({counts_text}). "
        "Use a professional UI layout, dark slate and cyan color palette."
    )
    dashboard_img = genai.image.generate(prompt=dashboard_prompt, size="1024x1024")

    # 2️⃣ time-distribution card
    time_prompt = (
        f"Create a pie or donut chart style image showing time spent per category: {duration_text}. "
        "Use soft colors and labels."
    )
    time_img = genai.image.generate(prompt=time_prompt, size="1024x1024")

    dashboard_path, time_path = "weekly_dashboard.png", "weekly_time_chart.png"
    dashboard_img.save(dashboard_path)
    time_img.save(time_path)
    return dashboard_path, time_path

# ========= TEXT SUMMARIES =========
def generate_descriptions(data):
    model = genai.GenerativeModel("models/gemini-2.0-pro")
    pie_prompt = f"Describe how the user spent time among these tasks: {list(data['durations'].items())}."
    bar_prompt = f"Summarize which days had the most events: {list(data['counts'].items())}."
    week_prompt = "Give a concise 3-sentence weekly productivity summary."
    pie_desc = model.generate_content(pie_prompt).text
    bar_desc = model.generate_content(bar_prompt).text
    week_desc = model.generate_content(week_prompt).text
    return pie_desc, bar_desc, week_desc

# ========= NOTION INTEGRATION =========
def upload_to_notion(database_id, summary_json):
    """Add the weekly summary as a Notion page with image links."""
    notion.pages.create(
        parent={"database_id": database_id},
        properties={
            "Name": {"title": [{"text": {"content": "Weekly Summary"}}]},
            "Summary": {"rich_text": [{"text": {"content": summary_json['weekly_summary']}}]},
            "Pie Desc": {"rich_text": [{"text": {"content": summary_json['pie_chart_description']}}]},
            "Bar Desc": {"rich_text": [{"text": {"content": summary_json['bar_chart_description']}}]},
        },
        children=[
            {"object": "block", "type": "image", "image": {"external": {"url": summary_json["pie_chart"]}}},
            {"object": "block", "type": "image", "image": {"external": {"url": summary_json["bar_chart"]}}},
        ],
    )

# ========= MAIN =========
def main():
    service = get_calendar_service()
    events = get_past_week_events(service)
    if not events:
        print("No events found this week.")
        return

    data = summarize_events(events)
    dash_img, time_img = generate_visuals(data)
    pie_desc, bar_desc, week_desc = generate_descriptions(data)

    summary = {
        "pie_chart": time_img,
        "bar_chart": dash_img,
        "pie_chart_description": pie_desc,
        "bar_chart_description": bar_desc,
        "weekly_summary": week_desc,
    }

    with open("weekly_report.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)
    print("✅ Weekly visual report generated and saved to weekly_report.json")

    # optional: push to Notion
    db_id = os.getenv("NOTION_DB_ID")
    if db_id:
        upload_to_notion(db_id, summary)
        print("🪄 Sent summary to Notion")

if __name__ == "__main__":
    main()
