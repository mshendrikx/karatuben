import requests
import json

url = 'http://localhost:5000/youtube_download/teste'
response = requests.get(url, timeout=10)

response_json = response.json()
api_response_status = response_json.get("status")