import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Copper API configuration
BASE_URL = "https://api.copper.com/developer_api/v1"
HEADERS = {
    "X-PW-AccessToken": os.getenv("COPPER_API_TOKEN"),
    "X-PW-Application": "developer_api",
    "X-PW-UserEmail": os.getenv("COPPER_EMAIL"),
    "Content-Type": "application/json"
}

def fetch_recent_leads():
    """
    Fetch the 3 most recent leads from Copper CRM
    """
    try:
        # Use the search endpoint to get leads sorted by creation date
        response = requests.post(
            f"{BASE_URL}/leads/search",
            headers=HEADERS,
            json={
                "page_size": 3,  # Limit to 3 results
                "sort_by": "date_created",  # Sort by creation date
                "sort_direction": "desc"    # Most recent first
            }
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse response JSON
        leads = response.json()
        
        if leads and len(leads) > 0:
            print(f"Found {len(leads)} recent leads:")
            
            # Display the leads with ALL information
            for i, lead in enumerate(leads, 1):
                print(f"\n{'='*50}")
                print(f"LEAD {i} - COMPLETE DETAILS")
                print(f"{'='*50}")
                
                # Print all fields in a readable format
                for field, value in lead.items():
                    # Format timestamps as readable dates
                    if field.startswith('date_') and isinstance(value, (int, float)):
                        formatted_value = datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')
                        print(f"{field}: {formatted_value}")
                    # Format nested dictionaries and lists with indentation
                    elif isinstance(value, (dict, list)):
                        print(f"{field}:")
                        print(json.dumps(value, indent=4))
                    # Print other values normally
                    else:
                        print(f"{field}: {value}")
            
            return leads
        else:
            print("No leads found.")
            return []
            
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP Error occurred: {http_err}")
        print(f"Response: {response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection Error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout Error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"Request Exception occurred: {req_err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    return None

if __name__ == "__main__":
    print("Fetching the 3 most recent leads from Copper CRM...")
    fetch_recent_leads()
    print("\nDone!")