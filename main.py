import requests

event_id = "15479162"

url = f"https://api.sofascore.com/api/v1/event/{event_id}/graph"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)

print(response.status_code)
print(response.json())
