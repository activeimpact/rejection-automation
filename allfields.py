import requests
import os
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()
COPPER_API_TOKEN = os.getenv("COPPER_API_TOKEN")
COPPER_EMAIL = os.getenv("COPPER_EMAIL")

# Copper API settings
COPPER_API_URL = "https://api.copper.com/developer_api/v1"
HEADERS = {
    "X-PW-AccessToken": COPPER_API_TOKEN,
    "X-PW-UserEmail": COPPER_EMAIL,
    "X-PW-Application": "developer_api",
    "Content-Type": "application/json"
}

# Function to fetch activity logs
def fetch_activity_logs():
    payload = {
        "page_size": 25,  # Fetch recent 25 activities
        "full_result": True  # Improve search performance
    }

    response = requests.post(f"{COPPER_API_URL}/activities/search", headers=HEADERS, json=payload)

    if response.status_code == 200:
        activities = response.json()
        if not activities:
            print("No recent activities found.")
            return []

        print("\nRecent Activity Logs:")
        for activity in activities:
            print(f"- Type: {activity.get('type', 'Unknown')} | "
                  f"Parent Type: {activity.get('parent', {}).get('type', 'N/A')} | "
                  f"Parent ID: {activity.get('parent', {}).get('id', 'N/A')} | "
                  f"Date: {activity.get('activity_date', 'Unknown')}")

        return activities
    else:
        print("Error fetching activity logs:", response.text)
        return []

# Run the function
fetch_activity_logs()
