from notion_client import Client
import os
from dotenv import load_dotenv

load_dotenv()

# --- Setup ---
NOTION_TOKEN = os.getenv("NOTION_TOKEN") or "paste-your-token-here"
DATABASE_ID = os.getenv("NOTION_NOTES_DB_ID")# Replace with your database ID

notion = Client(auth=NOTION_TOKEN)

print("🔍 Testing Notion API connection...")
print("Token starts with:", NOTION_TOKEN[:8], "...")

print("\n🔍 Searching all accessible databases...")
res = notion.search(filter={"property": "object", "value": "database"})


print("\n🧱 Database schema:")
props = res["results"][0]["properties"]
for key, val in props.items():
    print(f"- {key}: {val['type']}")


for db in res["results"]:
    print(f"- {db['title'][0]['plain_text']}: {db['id']}")

try:
    # --- Try querying the database ---
    res = notion.databases.query(database_id=DATABASE_ID)
    print("✅ Query succeeded!")
    print("Number of results:", len(res["results"]))
    for item in res["results"][:3]:
        title_prop = "Doc name"
        title_field = item["properties"][title_prop]["title"]
        title = title_field[0]["plain_text"] if title_field else "Untitled"
        print("-", title)
except Exception as e:
    print("❌ Error occurred:")
    print(type(e).__name__, "→", str(e))
