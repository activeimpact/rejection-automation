# Investment Pass Email Manager

A Streamlit application to manage and send rejection emails to investment leads from Copper CRM.

## Features

- Fetch leads from Copper CRM
- View detailed lead information
- Draft and send rejection emails with customizable templates
- (Windows only) Integration with Outlook to fetch form submission emails

## Local Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   
   For Windows users who want Outlook integration:
   ```
   pip install pywin32
   ```

3. Create a `.env` file with your credentials:
   ```
   COPPER_API_TOKEN=your_token_here
   COPPER_EMAIL=your_email_here
   OPENAI_API_KEY=your_key_here
   EMAIL_ADDRESS=your_email_here
   EMAIL_PASSWORD=your_app_password_here
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   ```

4. Run the application:
   ```
   streamlit run faith10-email-only.py
   ```

## Streamlit Cloud Deployment

1. Push this repository to GitHub
2. Create a Streamlit Cloud account and connect to your repository
3. Set up secrets in the Streamlit Cloud dashboard with the same keys as in the `.env` file
4. Deploy the app

## Note on Outlook Integration

The Outlook integration features only work when running on Windows with Outlook installed.
When deployed to Streamlit Cloud, these features will be automatically disabled.

## Security Considerations

- Never commit your `.env` file or `.streamlit/secrets.toml` file to Git
- Use Streamlit's authentication features to protect your deployed app
- Consider restricting access to specific Google accounts or domains

## Setup Instructions

1. Make sure you have Python 3.7+ installed on your system.

2. Install the required dependencies:
   ```
   pip install streamlit requests openai python-dotenv
   ```

3. Configure your environment variables by creating a `.env` file with the following variables:
   ```
   COPPER_API_TOKEN=your_copper_api_token
   COPPER_EMAIL=your_copper_email
   OPENAI_API_KEY=your_openai_api_key
   EMAIL_ADDRESS=your_outlook_email
   EMAIL_PASSWORD=your_outlook_password
   ```

   **Important Note about Email Password**: 
   - For Outlook/Office 365, you might need to use an "App Password" instead of your regular password.
   - To create an App Password, go to your Microsoft Account > Security > Advanced Security Options > App passwords.

4. Make sure your `email_templates.json` file is in the same directory as the application.

## Running the Application

1. Run the application with:
   ```
   streamlit run faith10-email-only.py
   ```

2. The application will open in your web browser.

## Testing Email Functionality

If you're having issues with email sending, you can test the email connection separately:

1. Run the test script:
   ```
   python test_email.py
   ```

2. This will test your email connection and optionally send a test email.

## Using the Application

1. **Email Configuration**: Check the sidebar to verify your email is properly configured.

2. **Select a Lead**: Choose a lead from the dropdown menu.

3. **Select Rejection Reason**: Choose the appropriate reason for rejection.

4. **Generate Email**: Click "Generate Rejection Email" to create a draft based on your templates.

5. **Edit Email**: Review and edit the email subject and content as needed.

6. **Send Email**: Click "Send Email" to send the rejection email.

7. **Clear and Start New**: After sending, you can clear the form to start with a new lead.

## Troubleshooting

### Email Authentication Issues

The most common issue is email authentication failing with Outlook/Office 365. If you see an error like "Authentication unsuccessful", try these solutions:

1. **Use an App Password instead of your regular password**:
   - Go to https://account.microsoft.com/security
   - Select "Advanced security options"
   - Under "Additional security", select "App passwords"
   - Create a new app password and use it in your `.env` file

2. **Enable Modern Authentication**:
   - Make sure your Microsoft 365 account has Modern Authentication enabled
   - Contact your IT administrator if needed

3. **Check for Multi-Factor Authentication (MFA)**:
   - If your account has MFA enabled, you MUST use an App Password

4. **Try a different email service**:
   - If Outlook continues to cause issues, consider using a different email service like Gmail

### Other Common Issues

1. **Check your .env file**:
   - Make sure all required variables are set correctly
   - There should be no spaces around the equals sign
   - Don't use quotes around values

2. **Verify network connectivity**:
   - Make sure your network allows SMTP connections to Outlook servers
   - Some corporate networks block these connections

3. **Check logs**:
   - Look for detailed error messages in the application logs
   - Run `test_email.py` for more verbose debugging information

4. **Restart the application**:
   - Sometimes simply restarting the application can resolve issues

## Zapier Integration

The application formats email subjects in a way that Zapier can recognize to automatically convert leads to opportunities in the "Pass General" stage. The subject format is:

```
PASS - {Company Name} - {Rejection Reason}
```

Configure your Zapier integration to trigger on emails with this subject pattern. 