# Active Impact Investments - Rejection Email Manager

This Streamlit application helps manage and send rejection emails to leads from the Active Impact Investments form submissions.

## Features

- View and search leads from Copper CRM
- Generate personalized rejection emails based on templates
- Send emails via SMTP
- Track email sending status
- Debug field mappings and custom fields

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.streamlit/secrets.toml`:
   ```toml
   COPPER_API_TOKEN = "your_token"
   COPPER_EMAIL = "your_email"
   OPENAI_API_KEY = "your_key"
   EMAIL_ADDRESS = "your_email"
   EMAIL_PASSWORD = "your_password"
   SMTP_SERVER = "smtp.gmail.com"
   SMTP_PORT = 587
   COPPER_API_URL = "https://api.copper.com/developer_api/v1"
   ```

## Running Locally

```bash
streamlit run streamlit-cloud-app.py
```

## Deployment

This app is deployed on Streamlit Cloud. To deploy:

1. Push your code to GitHub
2. Connect your repository to Streamlit Cloud
3. Set up the secrets in Streamlit Cloud's secrets management
4. Deploy the app

## File Structure

- `streamlit-cloud-app.py`: Main application file
- `email_templates.json`: Email templates for different rejection reasons
- `requirements.txt`: Python dependencies
- `.streamlit/config.toml`: Streamlit configuration
- `.gitignore`: Git ignore rules

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Submit a pull request

## License

Proprietary - All rights reserved 
