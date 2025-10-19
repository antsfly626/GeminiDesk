from notion_client import Client

# Initialize Notion client
notion = Client(auth="")

def main():
    # Example: list databases in your workspace
    response = notion.search(filter={"property": "object", "value": "database"})
    print("Available Databases:")
    for db in response["results"]:
        print("-", db["title"][0]["plain_text"] if db["title"] else "(Untitled)")

if __name__ == "__main__":
    main()
