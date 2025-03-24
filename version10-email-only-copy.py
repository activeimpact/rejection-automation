import streamlit as st

# Set page configuration for better appearance
st.set_page_config(
    page_title="Investment Pass Email Manager",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

import requests
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import datetime, timedelta
import re
import html
import time

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to get secrets from Streamlit or environment variables
def get_secret(key, default=None):
    """Get a secret from Streamlit secrets or environment variables with fallback to default."""
    try:
        # Try to access st.secrets first
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception as e:
        # Log the error but continue to fall back to environment variables
        logger.info(f"Streamlit secrets not available for {key}: {str(e)}. Using environment variables instead.")
    
    # Fall back to environment variables
    return os.getenv(key, default)

# Set up API credentials using get_secret
COPPER_API_TOKEN = get_secret('COPPER_API_TOKEN', '')
COPPER_EMAIL = get_secret('COPPER_EMAIL', '')
EMAIL_ADDRESS = get_secret('EMAIL_ADDRESS', '')
EMAIL_PASSWORD = get_secret('EMAIL_PASSWORD', '')
SMTP_SERVER = get_secret('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(get_secret('SMTP_PORT', '587'))
COPPER_API_URL = get_secret('COPPER_API_URL', 'https://api.copper.com/developer_api/v1')

# Log the credentials we're using (with appropriate masking)
logger.info("=== Copper API Configuration ===")
logger.info(f"Copper Email: {COPPER_EMAIL}")
if COPPER_API_TOKEN:
    masked_token = COPPER_API_TOKEN[:4] + "..." + COPPER_API_TOKEN[-4:] if len(COPPER_API_TOKEN) > 8 else "***"
    logger.info(f"Copper API Token (masked): {masked_token}")
    logger.info(f"Copper API Token length: {len(COPPER_API_TOKEN)} characters")
else:
    logger.warning("Copper API Token is not set")
logger.info(f"Copper API URL: {COPPER_API_URL}")
logger.info("================================")

# Log email configuration (without password)
logger.info(f"Email configuration: Address={EMAIL_ADDRESS}, Server={SMTP_SERVER}, Port={SMTP_PORT}")
if EMAIL_PASSWORD:
    masked_password = EMAIL_PASSWORD[:2] + "..." + EMAIL_PASSWORD[-2:] if len(EMAIL_PASSWORD) > 4 else "***"
    logger.info(f"Email password length: {len(EMAIL_PASSWORD)} characters")
else:
    logger.warning("Email password is not set")

# Set up API headers with the loaded credentials
HEADERS = {
    "X-PW-AccessToken": COPPER_API_TOKEN,
    "X-PW-UserEmail": COPPER_EMAIL,
    "X-PW-Application": "developer_api",
    "Content-Type": "application/json"
}

# Load rejection email templates from JSON file
import os

# Try different possible locations for the email_templates.json file
possible_paths = [
    "email_templates.json",
    os.path.join(os.path.dirname(__file__), "email_templates.json"),
    "/mount/src/rejection-automation/email_templates.json"  # Streamlit Cloud path
]

EMAIL_TEMPLATES = {}
for path in possible_paths:
    try:
        with open(path, "r") as f:
            EMAIL_TEMPLATES = json.load(f)
            logger.info(f"Loaded {len(EMAIL_TEMPLATES)} email templates from {path}")
            break
    except Exception as e:
        logger.warning(f"Couldn't load email templates from {path}: {e}")

# If no templates were loaded, provide defaults
if not EMAIL_TEMPLATES:
    logger.warning("Using default email templates")
    EMAIL_TEMPLATES = {
        "general": """Hi {first_name},\n\nThanks so much for reaching out to Active Impact!\n\nThank you for your interest in our fund, but we've decided to pass on this opportunity.\n\nWarmly,"""
    }

# Add global caching for lead details and field definitions
LEAD_DETAILS_CACHE = {}
FIELD_DEFINITIONS_CACHE = None

# Function to test email connection with detailed error reporting
def test_email_connection():
    """Test email connection with detailed error reporting."""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        return False, "Email credentials not configured. Please check your Streamlit secrets."
    
    try:
        logger.info(f"Attempting to connect to {SMTP_SERVER}:{SMTP_PORT}")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.set_debuglevel(1)  # Enable debug output
        server.starttls()
        
        logger.info(f"Attempting to login with email: {EMAIL_ADDRESS}")
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        
        server.quit()
        return True, "Email connection successful!"
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"Authentication failed: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Connection failed: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

# Function to fetch leads from Copper CRM with detailed error reporting
def fetch_leads():
    """Fetch leads from Copper CRM with detailed error reporting."""
    try:
        logger.info("Attempting to fetch leads from Copper")
        logger.info(f"Using API URL: {COPPER_API_URL}")
        logger.info(f"Using headers: {HEADERS}")
        
        response = requests.get(
            f"{COPPER_API_URL}/leads/search",
            headers=HEADERS,
            timeout=30
        )
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        
        if response.status_code == 401:
            logger.error("Authentication failed with Copper API")
            return {"error": "authentication error"}
        elif response.status_code != 200:
            logger.error(f"Error response from Copper: {response.text}")
            return {"error": f"API error: {response.status_code}"}
            
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"error": str(e)}

# Function to fetch custom field definitions from Copper
def fetch_custom_field_definitions():
    global FIELD_DEFINITIONS_CACHE
    
    # Return cached definitions if available
    if FIELD_DEFINITIONS_CACHE is not None:
        return FIELD_DEFINITIONS_CACHE
    
    response = requests.get(f"{COPPER_API_URL}/custom_field_definitions", headers=HEADERS)
    
    if response.status_code == 200:
        definitions = response.json()
        logger.info(f"Successfully fetched {len(definitions)} custom field definitions from Copper")
        
        # Create a dictionary mapping definition IDs to names
        definition_map = {}
        for definition in definitions:
            definition_map[definition.get("id")] = definition.get("name")
        
        # Store in global cache
        FIELD_DEFINITIONS_CACHE = definition_map
        return definition_map
    else:
        error_msg = f"Error fetching custom field definitions: {response.text}"
        st.error(error_msg)
        logger.error(error_msg)
        return {}

# Function to fetch lead details
def fetch_lead_details(lead_id):
    global LEAD_DETAILS_CACHE
    
    # Return cached details if available
    if lead_id in LEAD_DETAILS_CACHE:
        return LEAD_DETAILS_CACHE[lead_id]
    
    # Add the custom_field_computed_values=true parameter to get actual values for dropdown fields
    response = requests.get(f"{COPPER_API_URL}/leads/{lead_id}?custom_field_computed_values=true", headers=HEADERS)

    if response.status_code == 200:
        lead_details = response.json()
        logger.info(f"Successfully fetched details for lead ID: {lead_id}")
        
        # Store in global cache
        LEAD_DETAILS_CACHE[lead_id] = lead_details
        return lead_details
    else:
        error_msg = f"Error fetching lead details: {response.text}"
        st.error(error_msg)
        logger.error(error_msg)
        return {}

# Function to safely extract custom field values from Copper CRM data
def get_custom_field(lead_details, field_name):
    custom_fields = lead_details.get("custom_fields", [])

    if not custom_fields:
        return ""

    if isinstance(custom_fields, list):
        for field in custom_fields:
            if isinstance(field, dict) and field.get("name") == field_name:
                # Use computed_value if available, otherwise fall back to value
                if "computed_value" in field:
                    computed_value = field.get("computed_value")
                    # If computed_value is a list, join it with commas
                    if isinstance(computed_value, list):
                        return ", ".join(str(item) for item in computed_value)
                    return computed_value
                return field.get("value", "")  

    elif isinstance(custom_fields, dict):
        return custom_fields.get(field_name, "")

    return ""

def get_sender_name(email):
    """Extract first name from email address."""
    try:
        # Split email at @ and get the part before it
        local_part = email.split('@')[0]
        # Get the first name by removing the last character (which is the last initial)
        first_name = local_part[:-1] if len(local_part) > 1 else local_part
        # Capitalize first letter
        return first_name.capitalize()
    except:
        return "Active Impact"

def generate_rejection_email(lead_data, template_type="standard"):
    """Generate rejection email content based on lead data and template type."""
    try:
        # Get the template
        template = EMAIL_TEMPLATES.get(template_type, EMAIL_TEMPLATES.get("standard", ""))
        if not template:
            logger.error(f"Template not found: {template_type}")
            return None

        # Get sender's first name for signature
        sender_name = get_sender_name(EMAIL_ADDRESS)
        
        # Replace placeholders with actual data
        email_content = template.replace("{lead_name}", lead_data.get("name", ""))
        email_content = email_content.replace("{company_name}", lead_data.get("company_name", ""))
        email_content = email_content.replace("{sender_name}", sender_name)
        
        # Add signature
        email_content += f"\n\nWarmly,\n{sender_name}"
        
        return email_content
    except Exception as e:
        logger.error(f"Error generating email: {str(e)}")
        return None

# Function to extract email address from lead details
def get_email_from_lead(lead_details):
    # Try to get email from the email field
    email_obj = lead_details.get("email", {})
    if isinstance(email_obj, dict) and "email" in email_obj:
        return email_obj.get("email")
    
    # If that fails, try to get from emails array
    emails = lead_details.get("emails", [])
    if emails and isinstance(emails, list) and len(emails) > 0:
        for email in emails:
            if isinstance(email, dict) and "email" in email:
                return email.get("email")
    
    # If that fails, try to get from contact info
    contact_info = lead_details.get("contact_info", {})
    if isinstance(contact_info, dict) and "email" in contact_info:
        return contact_info.get("email")
    
    return ""

# Function to send email via Gmail SMTP
def send_email(recipient_email, subject, body, cc_email=None):
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        error_msg = "Email credentials not configured. Please check your Streamlit secrets."
        logger.error(error_msg)
        return False, error_msg
    
    if not recipient_email:
        error_msg = "No recipient email provided"
        logger.error(error_msg)
        return False, error_msg
    
    logger.info(f"Attempting to send email to: {recipient_email}")
    if cc_email:
        logger.info(f"CC: {cc_email}")
    logger.info(f"Email subject: {subject}")
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Add CC if provided
        if cc_email:
            msg['Cc'] = cc_email
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.set_debuglevel(1)  # Enable debug output
        server.starttls()
        
        logger.info(f"Attempting to login with email: {EMAIL_ADDRESS}")
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        
        text = msg.as_string()
        
        # Determine all recipients (including CC if provided)
        recipients = [recipient_email]
        if cc_email:
            recipients.append(cc_email)
        
        logger.info(f"Sending email from {EMAIL_ADDRESS} to {recipient_email}")
        server.sendmail(EMAIL_ADDRESS, recipients, text)
        server.quit()
        
        logger.info("Email sent successfully!")
        return True, "Email sent successfully!"
    except smtplib.SMTPAuthenticationError as e:
        if "535" in str(e):
            error_msg = (
                "Authentication failed with Gmail. This is likely because:\n"
                "1. You need to use an App Password instead of your regular password\n"
                "2. Your account has 2-factor authentication enabled which requires an App Password\n"
                "3. Your password may be incorrect\n\n"
                "To create an App Password:\n"
                "1. Go to your Google Account settings\n"
                "2. Search for 'App Passwords'\n"
                "3. Generate a new app password for 'Mail'\n"
                "4. Use that password in your Streamlit secrets"
            )
        else:
            error_msg = f"Authentication failed: {str(e)}. Please check your email credentials."
        logger.error(error_msg)
        return False, error_msg
    except smtplib.SMTPSenderRefused as e:
        error_msg = f"Sender refused: {str(e)}. This may be due to restrictions on your Gmail account."
        logger.error(error_msg)
        return False, error_msg
    except smtplib.SMTPRecipientsRefused as e:
        error_msg = f"Recipient(s) refused: {str(e)}. Please check the recipient email address."
        logger.error(error_msg)
        return False, error_msg
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

# Function to format timestamp to readable date
def format_date(timestamp):
    if not timestamp:
        return "Unknown date"
    try:
        # Convert milliseconds to seconds if needed
        if timestamp > 1000000000000:  # If timestamp is in milliseconds
            timestamp = timestamp / 1000
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.error(f"Error formatting date: {e}")
        return "Date format error"

# Function to calculate days in Copper
def days_in_copper(timestamp):
    if not timestamp:
        return "Unknown"
    try:
        # Convert milliseconds to seconds if needed
        if timestamp > 1000000000000:  # If timestamp is in milliseconds
            timestamp = timestamp / 1000
        
        created_date = datetime.fromtimestamp(timestamp)
        current_date = datetime.now()
        days = (current_date - created_date).days
        
        return days
    except Exception as e:
        logger.error(f"Error calculating days in Copper: {e}")
        return "Unknown"

# Function to determine lead source with improved detection
def get_lead_source(lead_details):
    # Check for form submission indicators
    
    # Check if there's a form submission tag
    tags = lead_details.get("tags", [])
    if any("form" in tag.lower() for tag in tags):
        return "Form Submission"
    
    # Check if there's a form submission in the source field
    source = lead_details.get("source", {})
    if isinstance(source, dict) and source.get("name"):
        source_name = source.get("name", "").lower()
        if "form" in source_name or "website" in source_name or "submission" in source_name:
            return "Form Submission"
    
    # Check custom fields for source information
    source_info = get_custom_field(lead_details, "Source")
    if source_info and ("form" in source_info.lower() or "website" in source_info.lower()):
        return "Form Submission"
    
    # Check if lead has many filled custom fields (likely from a form)
    custom_fields = lead_details.get("custom_fields", [])
    if isinstance(custom_fields, list) and len(custom_fields) > 5:
        filled_fields = sum(1 for field in custom_fields if isinstance(field, dict) and field.get("value"))
        if filled_fields > 5:  # If more than 5 custom fields are filled, likely a form submission
            return "Form Submission"
    
    # Check if specific form fields are present
    form_indicator_fields = ["Revenue Model", "Last year's revenue", "Number of full time employees"]
    if any(get_custom_field(lead_details, field) for field in form_indicator_fields):
        return "Form Submission"
    
    # If none of the above, it was likely manually added
    return "Manually Added"

# Function to determine if a lead likely has form data
def has_form_data(lead_details):
    # Check if there are any non-empty custom fields
    custom_fields = lead_details.get("custom_fields", [])
    if not custom_fields:
        return False
    
    for field in custom_fields:
        if isinstance(field, dict) and field.get('value') is not None and field.get('value') != "":
            return True
    
    return False

# Function to verify Copper API configuration
def verify_copper_config():
    """Verify Copper API configuration and connection."""
    if not COPPER_API_TOKEN or not COPPER_EMAIL:
        return False, "Copper API credentials not configured. Please check your Streamlit secrets."
    
    try:
        # Try to fetch a single lead to verify the connection
        response = requests.get(
            f"{COPPER_API_URL}/leads/search",
            headers=HEADERS,
            params={"page_size": 1},
            timeout=30
        )
        
        logger.info(f"Copper API Response Status: {response.status_code}")
        logger.info(f"Copper API Response Headers: {response.headers}")
        
        if response.status_code == 401:
            logger.error("Authentication failed with Copper API")
            return False, "Authentication failed with Copper API. Please check your API token and email."
        elif response.status_code != 200:
            logger.error(f"Error response from Copper: {response.text}")
            return False, f"API error: {response.status_code}. Please check your API configuration."
        
        return True, "Copper API configuration verified successfully!"
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return False, f"Connection error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False, f"Unexpected error: {str(e)}"

# Main Streamlit app
def main():
    # Initialize session state variables
    if "selected_leads" not in st.session_state:
        st.session_state.selected_leads = {}
    
    if "email_cache" not in st.session_state:
        st.session_state.email_cache = {}
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .days-in-copper {
        color: #FF4B4B;
        font-weight: bold;
    }
    .form-submission {
        color: #0068C9;
        font-weight: bold;
    }
    .manual-entry {
        color: #83C9FF;
        font-weight: bold;
    }
    .lead-header {
        font-size: 16px;
        font-weight: bold;
    }
    .custom-field-name {
        font-weight: bold;
        color: #555555;
    }
    .custom-field-value {
        margin-left: 10px;
    }
    .section-divider {
        margin-top: 20px;
        margin-bottom: 20px;
        border-bottom: 1px solid #EEEEEE;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("Investment Pass Email Manager")
    
    # Add field mapping debug page in sidebar
    st.sidebar.header("Settings")
    if st.sidebar.checkbox("Field ID Mapping Tool", value=False):
        st.header("Field ID Mapping Tool")
        st.write("""
        This tool helps you update the field ID mapping if you've changed field names in Copper.
        It fetches all custom field definitions from Copper and lets you match them to the fields you want to display.
        """)
        
        if st.button("Fetch Custom Field Definitions from Copper"):
            with st.spinner("Fetching custom field definitions from Copper..."):
                # Fetch custom field definitions directly from Copper API
                response = requests.get(f"{COPPER_API_URL}/custom_field_definitions", headers=HEADERS)
                
                if response.status_code == 200:
                    definitions = response.json()
                    
                    # Create a table of all definitions
                    fields_data = []
                    for definition in definitions:
                        fields_data.append({
                            "Field ID": definition.get("id"),
                            "Field Name": definition.get("name"),
                            "Data Type": definition.get("data_type"),
                            "Available Values": ", ".join(definition.get("available_values", [])) if definition.get("available_values") else ""
                        })
                    
                    st.write(f"Found {len(fields_data)} custom field definitions in Copper.")
                    st.dataframe(fields_data)
                    
                    # Generate Python code for field_id_mapping
                    st.write("### Generated field_id_mapping Python Code")
                    st.write("Copy this code to update your field_id_mapping dictionary:")
                    
                    mapping_code = "field_id_mapping = {\n"
                    for definition in definitions:
                        field_name = definition.get("name")
                        field_id = definition.get("id")
                        mapping_code += f"    \"{field_name}\": {field_id},\n"
                    mapping_code += "}"
                    
                    st.code(mapping_code, language="python")
                    
                    # Save to a file if requested
                    if st.button("Save mapping to field_mapping.py"):
                        try:
                            with open("field_mapping.py", "w") as f:
                                f.write(mapping_code)
                            st.success("Saved mapping to field_mapping.py")
                        except Exception as e:
                            st.error(f"Error saving mapping: {str(e)}")
                else:
                    st.error(f"Error fetching custom field definitions: {response.text}")
        
        # Return to main app
        st.write("---")
        st.write("Return to the main app to continue working with leads.")
        return
    
    st.write("### Draft and Send Rejection Emails")

    # Add email configuration status
    st.sidebar.header("Email Configuration")
    email_status = "✅ Configured" if EMAIL_ADDRESS and EMAIL_PASSWORD else "❌ Not Configured"
    st.sidebar.write(f"Email Status: {email_status}")
    
    # Add a test connection button in the sidebar
    if st.sidebar.button("Test Email Connection"):
        with st.spinner("Testing email connection..."):
            try:
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                server.starttls()
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.quit()
                st.sidebar.success("✅ Connection successful!")
                logger.info("Email connection test successful")
            except Exception as e:
                st.sidebar.error(f"❌ Connection failed: {str(e)}")
                logger.error(f"Email connection test failed: {str(e)}")

    # Add Copper API verification in sidebar
    st.sidebar.header("API Configuration")
    if st.sidebar.button("Verify Copper API"):
        with st.spinner("Verifying Copper API configuration..."):
            success, message = verify_copper_config()
            if success:
                st.sidebar.success("✅ " + message)
            else:
                st.sidebar.error("❌ " + message)

    # Add a refresh button
    if st.button("Refresh Leads"):
        # Clear caches on refresh
        global LEAD_DETAILS_CACHE
        LEAD_DETAILS_CACHE = {}
        if 'email_cache' in st.session_state:
            del st.session_state.email_cache
        st.rerun()

    # Fetch leads with error handling
    leads_result = fetch_leads()
    if isinstance(leads_result, dict) and "error" in leads_result:
        st.error(f"Error fetching leads from Copper: {leads_result['error']}")
        return
    
    leads = leads_result if isinstance(leads_result, list) else []
    if not leads:
        st.warning("No leads found in Copper CRM.")
        return

    # Add search functionality
    search_query = st.text_input("Search leads by name or company:", "")
    
    # Filter leads based on search query
    if search_query:
        filtered_leads = [
            lead for lead in leads 
            if search_query.lower() in lead.get("name", "").lower() 
            or search_query.lower() in lead.get("company_name", "").lower()
        ]
    else:
        filtered_leads = leads
    
    st.write(f"### Showing {len(filtered_leads)} leads")
    
    # Pre-fetch field definitions once
    field_definitions = fetch_custom_field_definitions()
    
    # Create a mapping of form field names to their corresponding custom field definition IDs
    field_id_mapping = {
        "Number of full time employees": 328938,
        "How did you hear about us?": 328940,
        "Year Founded": 328941,
        "Revenue Model": 328943,
        "Last year's revenue": 328937,
        "Amount raised to date": 328950,
        "Target size of current raise": 328951,
        "Link to your investor deck": 328958,
        "Last three months' revenue": 328944,
        "Value of new sales signed last month": 328946,
        "Specific environmental impact": 328942,
        "Number of paid customers": 328945,
        "Cash on hand": 328948,
        "Brief Company Description": 328956,  # This appears to be "Biggest concerns" now
        "Monthly net burn": 328947,
        "Most impressive points": 328954,
        "Competitors": 328949,
        "Most likely exit and timing": 328957,
        "Biggest concerns": 328953
    }

    # Define the exact form fields to display in the specified order
    field_order = [
        "First Name",
        "Last Name",
        "Company Name",
        "Website",
        "Email",
        "HQ Address",
        "Country",
        "Address Line 1",
        "Address Line 2",
        "City",
        "Province",
        "Postal Code",
        "Year Founded", 
        "Brief Company Description",
        "How did you hear about us?",
        "Specific environmental impact",
        "Revenue Model",
        "Last year's revenue",
        "Last three months' revenue",
        "Value of new sales signed last month",
        "Number of full time employees",
        "Number of paid customers",
        "Cash on hand",
        "Monthly net burn",
        "Amount raised to date",
        "Target size of current raise",
        "Link to your investor deck"
    ]
    
    # Lazy load lead details - only fetch when needed
    for lead in filtered_leads:
        lead_name = lead.get("name", "Unknown")
        company_name = lead.get("company_name", "Unknown Company")
        lead_id = lead.get("id")
        
        # Calculate days in Copper
        days = days_in_copper(lead.get("date_created"))
        
        # Check if we have form data without fetching full details
        has_form_icon = ""
        if lead_id in LEAD_DETAILS_CACHE:
            lead_details = LEAD_DETAILS_CACHE[lead_id]
            has_data = has_form_data(lead_details)
            has_form_icon = "📝 " if has_data else ""
        
        # Create an expander for each lead
        with st.expander(f"{has_form_icon}{lead_name} - {company_name} - {days} days in Copper"):
            # Only fetch lead details when the expander is opened
            lead_details = fetch_lead_details(lead_id)
            
            # Check for form data now that we have details
            if not has_form_icon:
                has_data = has_form_data(lead_details)
                has_form_icon = "📝 " if has_data else ""
            
            # Determine source
            source = get_lead_source(lead_details)
            source_class = "form-submission" if source == "Form Submission" else "manual-entry"
            
            # Create columns for basic info
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Name:** {lead_details.get('name', 'Unknown')}")
                st.write(f"**Company:** {lead_details.get('company_name', 'Unknown Company')}")
                st.write(f"**Created:** {format_date(lead_details.get('date_created'))}")
                st.write(f"**Days in Copper:** <span class='days-in-copper'>{days}</span>", unsafe_allow_html=True)
                st.write(f"**Source:** <span class='{source_class}'>{source}</span>", unsafe_allow_html=True)
            
            with col2:
                # Extract and display email more reliably
                recipient_email = get_email_from_lead(lead_details)
                st.write(f"**Email:** {recipient_email or 'No email provided'}")
                
                # Display additional details if available
                if lead_details.get("phone_number"):
                    st.write(f"**Phone:** {lead_details.get('phone_number')}")
                
                if lead_details.get("website"):
                    st.write(f"**Website:** {lead_details.get('website')}")
            
            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
            
            # Display all custom fields in a comprehensive way
            st.write("### Form Details")
            
            # Create a formatted display that matches the email notification format
            st.markdown("""
            <style>
            .email-format {
                font-family: Arial, sans-serif;
                line-height: 1.5;
                padding: 10px;
                background-color: #f9f9f9;
                border-radius: 5px;
                border-left: 3px solid #0068C9;
            }
            .email-format p {
                margin: 5px 0;
            }
            .email-label {
                font-weight: bold;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Start building the email-like format
            email_content = f"""<div class="email-format">
            <p>Sent via form submission from <a href="https://activeimpactinvestments.com">Active Impact Investments</a></p>
            """
            
            # Create a dictionary to directly access fields by their definition ID
            field_by_id = {}
            for field in lead_details.get("custom_fields", []):
                if isinstance(field, dict) and field.get("custom_field_definition_id"):
                    field_def_id = field.get("custom_field_definition_id")
                    
                    # Use computed_value if available, otherwise fall back to value
                    if "computed_value" in field:
                        computed_value = field.get("computed_value")
                        # If computed_value is a list, join it with commas
                        if isinstance(computed_value, list):
                            field_value = ", ".join(str(item) for item in computed_value)
                        else:
                            field_value = computed_value
                    else:
                        field_value = field.get("value", "")
                    
                    field_by_id[field_def_id] = field_value

            # Add fields in the specified order - ONLY include fields from field_order list
            for field_name in field_order:
                value = "Not provided"
                
                # For standard fields, use the existing logic
                if field_name in ["First Name", "Last Name", "Company Name", "Website", "Email", "HQ Address", "Country", 
                                  "Address Line 1", "Address Line 2", "City", "Province", "Postal Code"]:
                    if field_name == "First Name":
                        value = lead_details.get("first_name", "Not provided")
                    elif field_name == "Last Name":
                        value = lead_details.get("last_name", "Not provided")
                    elif field_name == "Company Name":
                        value = lead_details.get("company_name", "Not provided")
                    elif field_name == "Website":
                        websites = lead_details.get("websites", [])
                        if websites and len(websites) > 0:
                            value = websites[0].get("url", "Not provided")
                        else:
                            value = "Not provided"
                    elif field_name == "Email":
                        value = get_email_from_lead(lead_details) or "Not provided"
                    # Handle address fields
                    elif field_name in ["HQ Address", "Country", "Address Line 1", "Address Line 2", "City", "Province", "Postal Code"]:
                        address = lead_details.get("address", {})
                        if field_name == "HQ Address":
                            address_parts = []
                            if address.get("street"):
                                address_parts.append(address.get("street", ""))
                            if address.get("city"):
                                address_parts.append(address.get("city", ""))
                            if address.get("state"):
                                address_parts.append(address.get("state", ""))
                            if address.get("postal_code"):
                                address_parts.append(address.get("postal_code", ""))
                            if address.get("country"):
                                address_parts.append(address.get("country", ""))
                            value = ", ".join(address_parts) if address_parts else "Not provided"
                        elif field_name == "Country":
                            value = address.get("country", "Not provided")
                        elif field_name == "Address Line 1":
                            value = address.get("street", "Not provided")
                        elif field_name == "Address Line 2":
                            value = "Not provided"  # Usually not in the API
                        elif field_name == "City":
                            value = address.get("city", "Not provided")
                        elif field_name == "Province":
                            value = address.get("state", "Not provided")
                        elif field_name == "Postal Code":
                            value = address.get("postal_code", "Not provided")
                # For custom fields, use the ID mapping
                elif field_name in field_id_mapping:
                    field_id = field_id_mapping[field_name]
                    if field_id in field_by_id and field_by_id[field_id] not in [None, ""]:
                        value = field_by_id[field_id]
                    else:
                        # Debug logging to understand why field is missing
                        logger.info(f"Field '{field_name}' (ID: {field_id}) not found in lead data")
                
                # If value is still None or empty, show as not provided
                if value is None or value == "":
                    value = "Not provided"
                    
                email_content += f"<p><span class='email-label'>{field_name}:</span> {value}</p>"
            
            # Close the form fields div
            email_content += "</div>"
            
            # Display the email-like format
            st.markdown(email_content, unsafe_allow_html=True)
            
            # Add debugging to show all available custom fields
            if st.checkbox("Debug Field IDs", value=False, key=f"debug_{lead_id}"):
                st.write("### Debug: Available Custom Fields")
                st.write("This shows all available custom fields and their IDs for this lead.")
                
                custom_fields_debug = []
                for field in lead_details.get("custom_fields", []):
                    if isinstance(field, dict):
                        field_id = field.get("custom_field_definition_id")
                        field_name = field_definitions.get(field_id, "Unknown Field")
                        
                        # Get the field value
                        if "computed_value" in field:
                            computed_value = field.get("computed_value")
                            if isinstance(computed_value, list):
                                field_value = ", ".join(str(item) for item in computed_value)
                            else:
                                field_value = computed_value
                        else:
                            field_value = field.get("value", "")
                            
                        custom_fields_debug.append({
                            "Field ID": field_id,
                            "Field Name": field_name,
                            "Value": field_value
                        })
                
                if custom_fields_debug:
                    st.table(custom_fields_debug)
                else:
                    st.write("No custom fields found for this lead.")
            
            # Add additional information from the lead if available
            if lead_details.get("details") or lead_details.get("description"):
                st.write("### Additional Information")
                if lead_details.get("details"):
                    st.write(lead_details.get("details"))
                if lead_details.get("description"):
                    st.write(lead_details.get("description"))
            
            # Close the current expander before creating a new one
            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
            
            # Add a button to select this lead for email
            if st.button(f"Draft Email for {lead_name}", key=f"select_{lead_id}"):
                # Initialize session state for this lead if not already done
                if "selected_leads" not in st.session_state:
                    st.session_state.selected_leads = {}
                
                # Mark this lead as selected and store its details
                st.session_state.selected_leads[lead_id] = {
                    "lead_details": lead_details,
                    "reason": "general"
                }
                
                # Force a rerun to show the email draft
                st.rerun()
            
            # Check if this lead is selected for email drafting
            if "selected_leads" in st.session_state and lead_id in st.session_state.selected_leads:
                # Display the email draft right here in the expander
                st.write("### Draft Rejection Email")
            
                # Rejection reason selection
                reason_options = {
                    "hardware": "Hardware (Pre-commercial or CapEx Intensive)",
                    "too_early": "Too Early but Could Be a Future Fit",
                    "geography": "Geography",
                    "too_far_along": "Too Far Along",
                    "not_enough_impact": "Not Enough Impact",
                    "competitive": "Competitive with Portfolio Companies",
                    "general": "General Pass"
                }
                
                # Get the current reason from session state
                current_reason = st.session_state.selected_leads[lead_id]["reason"]
                
                # Create a key that includes the current reason to force re-render when reason changes
                select_key = f"reason_select_{lead_id}_{current_reason}"
                
                # Create the selectbox for rejection reasons
                selected_reason = st.selectbox(
                    "Select Rejection Reason",
                    list(reason_options.keys()),
                    format_func=lambda x: reason_options[x],
                    index=list(reason_options.keys()).index(current_reason),
                    key=select_key
                )
                
                # Update the reason in session state if it changed
                if selected_reason != current_reason:
                    st.session_state.selected_leads[lead_id]["reason"] = selected_reason
                    # Clear the email cache for this lead to force regeneration
                    cache_key = f"{lead_id}_{current_reason}"
                    if cache_key in st.session_state.email_cache:
                        del st.session_state.email_cache[cache_key]
                    # Force a rerun to update the UI with the new reason
                    st.rerun()
                
                # Generate email content based on the selected reason
                with st.spinner("Generating rejection email..."):
                    email_content = generate_rejection_email(lead_details, selected_reason)
                    
                # Get recipient email more reliably
                recipient_email = get_email_from_lead(lead_details)
                
                # Display recipient email for verification
                st.write(f"**Sending to:** {recipient_email or 'No email found'}")
                
                # Create subject with pattern for Zapier to recognize
                # Always use the same subject line as requested
                email_subject = "Re: Active Impact Investments Form Submission"
                
                # Let user edit the subject
                edited_subject = st.text_input("Email Subject:", email_subject, key=f"subject_{lead_id}")
                
                # Add CC option
                cc_email = st.text_input("CC (optional):", "", key=f"cc_{lead_id}")
                
                # Let user edit the email content
                edited_content = st.text_area("Edit Email Content:", email_content, height=300, key=f"content_{lead_id}")
                
                # Send email button with confirmation
                if st.button("Send Email", key=f"send_{lead_id}"):
                    if not recipient_email:
                        st.error("No recipient email address found for this lead.")
                    elif not EMAIL_ADDRESS or not EMAIL_PASSWORD:
                        st.error("Email credentials not configured. Please check your Streamlit secrets.")
                    else:
                        # First verify connection
                        try:
                            with st.spinner("Verifying email connection..."):
                                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                                server.starttls()
                                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                                server.quit()
                                
                            # If connection is successful, send the email
                            with st.spinner("Sending email..."):
                                success, message = send_email(recipient_email, edited_subject, edited_content, cc_email)
                                
                            if success:
                                st.success(f"Email sent to {recipient_email}!")
                                if cc_email:
                                    st.success(f"CC'd to {cc_email}")
                                st.info("Zapier will now automatically convert the lead to an opportunity in the Pass 'General' stage.")
                                
                                # Log the successful email for debugging
                                logger.info(f"Email successfully sent to {recipient_email} with subject: {edited_subject}")
                                if cc_email:
                                    logger.info(f"CC'd to {cc_email}")
                                
                                # Remove this lead from selected leads after sending
                                del st.session_state.selected_leads[lead_id]
                            else:
                                st.error(message)
                                st.info("Please check the logs for more details on the error.")
                        except Exception as e:
                            st.error(f"Failed to connect to email server: {str(e)}")
                            logger.error(f"Email connection failed during send attempt: {str(e)}")
                
                # Add a cancel button to close the email draft
                if st.button("Cancel", key=f"cancel_{lead_id}"):
                    del st.session_state.selected_leads[lead_id]
                    st.rerun()
        
        # End of the lead expander

if __name__ == "__main__":
    main()
