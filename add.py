import json
import httpx  # pip install httpx

# Path to your JSON file
file_path = "data.json"

# FastAPI endpoint
url = "http://127.0.0.1:8000/plants/all"

# Load JSON data
with open(file_path, "r", encoding="utf-8") as f:
    plants_data = json.load(f)

# Send POST request
response = httpx.post(url, json=plants_data)

# Print server response
print(response.status_code)
print(response.json())
