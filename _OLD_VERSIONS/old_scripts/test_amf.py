
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

api_key = os.getenv("ANYMAILFINDER_API_KEY")
url = "https://api.anymailfinder.com/v5.1/find-email/person"
headers = {
    "Authorization": api_key,
    "Content-Type": "application/json"
}
body = {
    "first_name": "Matthew",
    "last_name": "Russo",
    "domain": "firstclasselectricnj.com"
}

response = requests.post(url, headers=headers, json=body)
print(json.dumps(response.json(), indent=2))
