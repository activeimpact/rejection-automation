import requests
import os
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()
COPPER_API_TOKEN = os.getenv("COPPER_API_TOKEN")
COPPER_EMAIL = os.getenv("COPPER_EMAIL")

COPPER_API_URL = "https://api.copper.com/developer_api/v1"
HEADERS = {
    "X-PW-AccessToken": COPPER_API_TOKEN,
    "X-PW-UserEmail": COPPER_EMAIL,
    "X-PW-Application": "developer_api",
    "Content-Type": "application/json"
}

opportunity_id = 33762876  # The missing opportunity ID

def get_opportunity_details():
    """Fetch details of the opportunity."""
    response = requests.get(f"{COPPER_API_URL}/opportunities/{opportunity_id}", headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print("Opportunity not found:", response.text)
        return None

def get_activity_logs():
    """Fetch activity logs related to the missing opportunity."""
    payload = {
        "parent": {"id": opportunity_id, "type": "opportunity"},
        "page_size": 10  # Fetch the latest 10 activities related to this opportunity
    }
    response = requests.post(f"{COPPER_API_URL}/activities/search", headers=HEADERS, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching activity logs:", response.text)
        return None

# Fetch opportunity details
opportunity_data = get_opportunity_details()
if opportunity_data:
    print("\n--- Opportunity Details ---")
    print(opportunity_data)

# Fetch activity logs related to the opportunity
activity_logs = get_activity_logs()
if activity_logs:
    print("\n--- Recent Activity Logs for Opportunity ---")
    for activity in activity_logs:
        print(f"- Type: {activity.get('type')}, Name: {activity.get('name')}, Date: {activity.get('activity_date')}")

