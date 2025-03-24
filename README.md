# Rejection Automation Tool

A Streamlit-based application for managing and automating investment rejection emails for Active Impact Investments.

## Features

- Lead management from Copper CRM
- Automated email generation with customizable templates
- Form submission tracking
- Email history and tracking
- Secure credential management

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the following variables:
   ```
   COPPER_API_TOKEN=your_token
   COPPER_EMAIL=your_email
   OPENAI_API_KEY=your_key
   EMAIL_ADDRESS=your_email
   EMAIL_PASSWORD=your_password
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   COPPER_API_URL=https://api.copper.com/developer_api/v1
   ```

## Usage

1. Run the Streamlit app:
   ```bash
   streamlit run version10-email-only-copy.py
   ```
2. Access the application through your web browser
3. Select leads from Copper CRM
4. Generate and send rejection emails

## Project Structure

- `version10-email-only-copy.py`: Main Streamlit application
- `email_templates.json`: Email templates for different rejection scenarios
- `flask/`: Flask version of the application (legacy)
- `.env`: Environment variables (not included in repository)

## Security

- All sensitive credentials are stored in environment variables
- API keys and passwords are never committed to the repository
- Email credentials are managed securely

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

Private - All rights reserved
