import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

ANYMAILFINDER_API_KEY = os.getenv("ANYMAILFINDER_API_KEY")
ANYMAILFINDER_BASE_URL = "https://api.anymailfinder.com/v5.1"

def test_decision_maker():
    if not ANYMAILFINDER_API_KEY:
        print("❌ API Key not found")
        return

    domain = "hlmedspa.com" # Using one of the leads from the previous hunt
    print(f"🚀 Testing Decision Maker API for: {domain}")
    
    payload = {
        "domain": domain,
        "decision_maker_category": ["ceo"]
    }
    
    try:
        response = requests.post(
            f"{ANYMAILFINDER_BASE_URL}/find-email/decision-maker",
            headers={
                "Authorization": f"Bearer {ANYMAILFINDER_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_decision_maker()
