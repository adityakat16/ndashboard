# app.py
from flask import Flask, jsonify, request
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import json
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# --- Google Sheets API Configuration ---
# IMPORTANT: DO NOT hardcode your service account credentials here.
# Use environment variables, especially in production environments like Render.
# The `__firebase_config` variable from Canvas runtime provides your Firebase
# (and implicitly GCP) credentials. If using a separate service account for
# Google Sheets API that is NOT tied to Firebase, ensure its JSON key is
# loaded securely via an environment variable (e.g., GOOGLE_SHEETS_SERVICE_ACCOUNT_KEY).

# Try to load credentials from the Canvas provided __firebase_config first,
# then fallback to a specific environment variable for Google Sheets,
# and finally try a local file for development.

service = None # Global variable to store the Google Sheets service object

# Define the scopes required for Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def initialize_google_sheets_service():
    """Initializes the Google Sheets API service using credentials."""
    global service # Indicate that we're modifying the global service variable
    logging.info("Attempting to initialize Google Sheets API service...")

    creds_found = False
    info = {} # Dictionary to hold credential info

    # Option 1: Use Canvas's __firebase_config (if it contains GCP service account creds)
    # This is often the most direct way if Firebase Auth is used and linked to GCP.
    if '__firebase_config' in globals() and __firebase_config:
        try:
            firebase_config_dict = json.loads(__firebase_config)
            # Assuming the 'private_key' and 'client_email' are present in this config
            info = {
                "type": firebase_config_dict.get("type", "service_account"),
                "project_id": firebase_config_dict.get("project_id"),
                "private_key_id": firebase_config_dict.get("private_key_id"),
                "private_key": firebase_config_dict.get("private_key"),
                "client_email": firebase_config_dict.get("client_email"),
                "client_id": firebase_config_dict.get("client_id"),
                "auth_uri": firebase_config_dict.get("auth_uri"),
                "token_uri": firebase_config_dict.get("token_uri"),
                "auth_provider_x509_cert_url": firebase_config_dict.get("auth_provider_x509_cert_url"),
                "client_x509_cert_url": firebase_config_dict.get("client_x509_cert_url"),
                "universe_domain": firebase_config_dict.get("universe_domain")
            }
            creds_found = True
            logging.info("Google Sheets API service attempting with __firebase_config.")
        except Exception as e:
            logging.error(f"Failed to parse __firebase_config: {e}")

    # Option 2: Load from a dedicated environment variable (e.g., for a separate Google Sheets service account)
    if not creds_found:
        google_creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if google_creds_json:
            try:
                info = json.loads(google_creds_json)
                creds_found = True
                logging.info("Google Sheets API service attempting with GOOGLE_CREDENTIALS_JSON env var.")
            except Exception as e:
                logging.error(f"Failed to parse GOOGLE_CREDENTIALS_JSON env var: {e}")

    # Option 3: Load from a local file (for local development only, NOT for Render deployment)
    if not creds_found and os.path.exists('service_account_key.json'):
        try:
            with open('service_account_key.json', 'r') as f:
                info = json.load(f)
            creds_found = True
            logging.info("Google Sheets API service attempting with local service_account_key.json.")
        except Exception as e:
            logging.error(f"Failed to read local service_account_key.json: {e}")

    if creds_found:
        try:
            # IMPORTANT FIX: Ensure private_key has actual newlines, not escaped ones.
            # This is a common issue when credentials are passed via environment variables.
            if 'private_key' in info and isinstance(info['private_key'], str):
                info['private_key'] = info['private_key'].replace('\\n', '\n')
                logging.info("Private key newlines replaced for proper parsing.")

            credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            service = build('sheets', 'v4', credentials=credentials)
            logging.info("Google Sheets API service initialized successfully.")
            return True
        except Exception as e:
            logging.error(f"Failed to initialize Google Sheets API service: {e}")
            service = None # Ensure service is None if initialization fails
            return False
    else:
        logging.error("Google Sheets API service could not be initialized. No valid credentials found from any source.")
        service = None
        return False

# Call initialization when the Flask app starts
initialize_google_sheets_service()

@app.route('/get_sheet_data', methods=['GET'])
def get_sheet_data():
    """
    Fetches data from a specified Google Sheet and returns it as JSON.
    """
    if not service:
        # Attempt to re-initialize if not already successful (e.g., if startup failed)
        # This re-initialization is primarily for development/debugging;
        # in production, you want successful init at startup.
        logging.warning("Google Sheets API service not initialized, attempting re-initialization.")
        if not initialize_google_sheets_service():
            return jsonify(status="error", message="Google Sheets API service not initialized and failed to re-initialize."), 500

    # --- IMPORTANT: Configure your Spreadsheet ID and Range here ---
    # You can get the Spreadsheet ID from the URL of your Google Sheet:
    # https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit
    SPREADSHEET_ID = '1pv6iqeAzQzu6eHaB_v46BQ1vsGM6MntUvJ9o7D9iWGI' # <<< REPLACE THIS
    # The range to fetch data from (e.g., 'Sheet1!A1:E10' or 'Inventory!A:Z')
    RANGE_NAME = 'Sheet1!A:E' # <<< REPLACE THIS with your sheet name and range

    if SPREADSHEET_ID == '1pv6iqeAzQzu6eHaB_v46BQ1vsGM6MntUvJ9o7D9iWGI':
        return jsonify(status="error", message="Please configure SPREADSHEET_ID in app.py"), 500

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        values = result.get('values', [])

        if not values:
            return jsonify(status="success", message="No data found in the specified range.", values=[]), 200
        else:
            return jsonify(status="success", message="Data fetched successfully.", values=values), 200

    except Exception as e:
        logging.error(f"Error fetching data from Google Sheet: {e}")
        return jsonify(status="error", message=f"Failed to fetch data from Google Sheet: {str(e)}"), 500

@app.route('/')
def home():
    """Serves the data.html file."""
    # In a real Flask app, you'd typically serve HTML templates from a 'templates' folder.
    # For this example, we'll assume data.html is in the same directory.
    # For a simple local serving, you might use:
    # from flask import send_from_directory
    # return send_from_directory('.', 'data.html')
    # Or for Canvas, if you are not running it locally, just ensure the frontend HTML
    # is deployed separately or served by a static file server.
    # The current setup expects `data.html` to be loaded directly by the Canvas environment.
    return "Backend is running. Access data.html directly in your Canvas environment."

if __name__ == '__main__':
    # This block is for local development only. Render will use its own entry point (gunicorn).
    # To run locally: python app.py
    # Ensure you have 'service_account_key.json' in the same directory for local testing.
    # You also need to install Flask and google-api-python-client:
    # pip install Flask google-api-python-client google-auth-oauthlib google-auth-httplib2
    logging.info("Starting Flask application in local development mode.")
    app.run(debug=True, host='0.0.0.0', port=os.getenv('PORT', 8080))
