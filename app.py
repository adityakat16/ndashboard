# app.py
from flask import Flask, jsonify, request, send_from_directory # Import send_from_directory
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import json
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# --- Google Sheets API Configuration ---
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
    if '__firebase_config' in globals() and __firebase_config:
        try:
            firebase_config_dict = json.loads(__firebase_config)
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
    It can now take 'sheet_name' and 'range_name' as query parameters.
    Example: /get_sheet_data?sheet_name=Annual&range_name=A1:F10
    To fetch the entire sheet, you can pass range_name='A:Z' (or 'A:ZZZ' for very wide sheets).
    """
    if not service:
        logging.warning("Google Sheets API service not initialized, attempting re-initialization.")
        if not initialize_google_sheets_service():
            return jsonify(status="error", message="Google Sheets API service not initialized and failed to re-initialize."), 500

    # --- IMPORTANT: Configure your Spreadsheet ID here ---
    # You can get the Spreadsheet ID from the URL of your Google Sheet:
    # https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit
    SPREADSHEET_ID = '1pv6iqeAzQzu6eHaB_v46BQ1vsGM6MntUvJ9o7D9iWGI' # <<< REPLACE THIS with your actual Spreadsheet ID

    if SPREADSHEET_ID == 'YOUR_SPREADSHEET_ID_HERE':
        return jsonify(status="error", message="Please configure SPREADSHEET_ID in app.py"), 500

    # Get sheet_name and range_name from query parameters, with defaults
    sheet_name = request.args.get('sheet_name', 'overall') # Default to 'overall'
    data_range = request.args.get('range_name', 'A:Z') # Default to 'A:Z' for entire sheet

    # Construct the full RANGE_NAME
    RANGE_NAME = f"{sheet_name}!{data_range}"
    logging.info(f"Fetching data from sheet: {sheet_name} with range: {data_range}")

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        values = result.get('values', [])

        if not values:
            return jsonify(status="success", message=f"No data found in {sheet_name} for range {data_range}.", values=[]), 200
        else:
            return jsonify(status="success", message="Data fetched successfully.", values=values), 200

    except Exception as e:
        logging.error(f"Error fetching data from Google Sheet ({RANGE_NAME}): {e}")
        return jsonify(status="error", message=f"Failed to fetch data from Google Sheet: {str(e)}"), 500

@app.route('/')
@app.route('/index.html')
def serve_index():
    """Serves the index.html file from the 'templates' directory."""
    return send_from_directory('templates', 'index.html')

@app.route('/data.html')
def serve_data_html():
    """Serves the data.html file from the 'templates' directory."""
    return send_from_directory('templates', 'data.html')

@app.route('/loading.html')
def serve_loading_html():
    """Serves the loading.html file from the 'templates' directory."""
    return send_from_directory('templates', 'loading.html')

# Add a route to serve static CSS/JS files if they are in a 'static' folder
# If you have a 'static' folder for CSS/JS, you might need something like this:
# @app.route('/static/<path:filename>')
# def serve_static(filename):
#     return send_from_directory('static', filename)


if __name__ == '__main__':
    # This block is for local development only. Render will use its own entry point (gunicorn).
    logging.info("Starting Flask application in local development mode.")
    # Ensure you are running from the root directory of your project for send_from_directory to find 'templates'
    app.run(debug=True, host='0.0.0.0', port=os.getenv('PORT', 8080))
