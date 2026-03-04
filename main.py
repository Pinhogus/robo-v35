import requests

event_id = "15479162"

url = f"https://api.sofascore.com/api/v1/event/{event_id}/graph"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "Connection": "keep-alive"
}

response = requests.get(url, headers=headers)

print(response.status_code)
print(response.text)
