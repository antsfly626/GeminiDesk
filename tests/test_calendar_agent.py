import requests

file_path = "d:/Projects/tedai-gemini-desk/data/events/pinterest_trip.txt"
with open(file_path, "r") as f:
    text = f.read().strip()

payload = {"text": text}
url = "http://127.0.0.1:8002/parse_event"

response = requests.post(url, json=payload)

print("Input text:\n", text)
print("\nResponse JSON:")
print(response.json())