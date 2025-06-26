# app.py
from flask import Flask, jsonify, request, send_from_directory
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import json
import logging
import requests # Make sure requests is imported at the top

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# --- Google Sheets API Configuration ---
service = None # Global variable to store the Google Sheets service object

# Define the scopes required for Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# =================================================================================
# NEW: Endpoint for Render to send input to your Local Machine via Ngrok
# This function is intended to run on your DEPLOYED Render app.
# =================================================================================
@app.route('/send_input', methods=['POST'])
def send_input():
    try:
        data = request.get_json()
        stock_symbol = data.get("stock_symbol")
        
        if not stock_symbol:
            return jsonify(status="error", message="Missing 'stock_symbol' in request."), 400

        # Get the ngrok URL from environment variable
        # This environment variable MUST be set on Render and contain your active Ngrok URL
        ngrok_url = os.environ.get('LOCAL_PROCESSOR_URL')
        if not ngrok_url:
            logging.error("LOCAL_PROCESSOR_URL environment variable is not set.")
            return jsonify(status="error", message="LOCAL_PROCESSOR_URL not set in environment variables."), 500

        # Construct full URL to your local endpoint that will process the input
        target_url = f"{ngrok_url}/process_input"
        logging.info(f"Attempting to send input to local machine at: {target_url}")

        # Send the data to your local machine
        response = requests.post(target_url, json={"stock_symbol": stock_symbol}, timeout=30) # Increased timeout for Ngrok latency

        # Check if the response from local machine is successful and contains JSON
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        
        # Try to parse the JSON response from your local machine
        local_response_data = response.json()
        logging.info(f"Successfully received response from local machine: {local_response_data}")

        # Forward the response back to the client that called /send_input
        return jsonify(status="success", message="Forwarded to local machine and received response.", data=local_response_data), 200

    except requests.exceptions.Timeout:
        logging.exception("Timeout connecting to local machine via Ngrok. Is Ngrok running and URL correct?")
        return jsonify(status="error", message="Request to local machine timed out. Is your local server and Ngrok running?"), 504
    except requests.exceptions.RequestException as e:
        logging.exception(f"Request error sending input to local machine via ngrok: {e}")
        return jsonify(status="error", message=f"Failed to connect to local machine: {e}"), 503
    except json.JSONDecodeError as e:
        logging.exception(f"JSONDecodeError from local machine response: {e}. Response text: {response.text}")
        return jsonify(status="error", message=f"Received non-JSON response from local machine: {response.text[:200]}"), 502 # Show part of response for debugging
    except Exception as e:
        logging.exception("An unexpected error occurred in /send_input:")
        return jsonify(status="error", message=str(e)), 500

# =================================================================================
# NEW: Endpoint for your LOCAL Flask app to receive input from Render
# This function is intended to run on your LOCAL computer, exposed by Ngrok.
# =================================================================================
@app.route('/process_input', methods=['POST'])
def process_input():
    """
    Receives input from the Render backend and processes it locally.
    This is where your local data processing logic (e.g., calling your ML model) would go.
    """
    try:
        data = request.get_json()
        stock_symbol = data.get("stock_symbol")

        if not stock_symbol:
            return jsonify(status="error", message="Missing 'stock_symbol' in local process_input request."), 400

        logging.info(f"Local machine received stock symbol for processing: {stock_symbol}")

        # --- YOUR LOCAL PROCESSING LOGIC GOES HERE ---
        # Example: Simulate some local processing
        processed_data = {
            "symbol": stock_symbol,
            "local_timestamp": "2025-06-26 10:00:00",
            "prediction_score": 0.85,
            "message": f"Processed '{stock_symbol}' successfully on local machine."
        }

        # For demonstration, we'll return this simulated data.
        # In a real scenario, this would involve your actual local ML model, etc.
        return jsonify(status="success", message="Data processed locally.", processed_data=processed_data), 200

    except Exception as e:
        logging.exception("Error processing input on local machine:")
        return jsonify(status="error", message=f"Local processing failed: {str(e)}"), 500

# =================================================================================
# Existing Google Sheets API Initialization
# =================================================================================
def initialize_google_sheets_service():
    """Initializes the Google Sheets API service using credentials."""
    global service 
    logging.info("Attempting to initialize Google Sheets API service...")

    creds_found = False
    info = {} 

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

    if not creds_found:
        google_creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if google_creds_json:
            try:
                info = json.loads(google_creds_json)
                creds_found = True
                logging.info("Google Sheets API service attempting with GOOGLE_CREDENTIALS_JSON env var.")
            except Exception as e:
                logging.error(f"Failed to parse GOOGLE_CREDENTIALS_JSON env var: {e}")

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
            if 'private_key' in info and isinstance(info['private_key'], str):
                info['private_key'] = info['private_key'].replace('\\n', '\n')
                logging.info("Private key newlines replaced for proper parsing.")

            credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            service = build('sheets', 'v4', credentials=credentials)
            logging.info("Google Sheets API service initialized successfully.")
            return True
        except Exception as e:
            logging.error(f"Failed to initialize Google Sheets API service: {e}")
            service = None
            return False
    else:
        logging.error("Google Sheets API service could not be initialized. No valid credentials found from any source.")
        service = None
        return False

initialize_google_sheets_service()

# =================================================================================
# Existing Google Sheets Data Fetching Endpoint
# =================================================================================
@app.route('/get_sheet_data', methods=['GET'])
def get_sheet_data():
    """
    Fetches data from a specified Google Sheet and returns it as JSON.
    It takes 'sheet_name' and 'range_name' as query parameters.
    """
    if not service:
        logging.warning("Google Sheets API service not initialized, attempting re-initialization.")
        if not initialize_google_sheets_service():
            return jsonify(status="error", message="Google Sheets API service not initialized and failed to re-initialize."), 500

    # SPREADSHEET_ID = '1pv6iqeAzQzu6eHaB_v46BQ1vsGM6MntUvJ9o7D9iWGI' # Use your actual ID
    # Ensure you replace this with your actual Google Sheet ID
    SPREADSHEET_ID = '1pv6iqeAzQzu6eHaB_v46BQ1vsGM6MntUvJ9o7D9iWGI' # Assuming this is your actual ID from previous logs

    if SPREADSHEET_ID == 'YOUR_SPREADSHEET_ID_HERE':
        return jsonify(status="error", message="Please configure SPREADSHEET_ID in app.py"), 500

    sheet_name = request.args.get('sheet_name', 'Overall') # Default to 'Overall'
    data_range = request.args.get('range_name', 'A:Z') # Default to 'A:Z' for entire sheet

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

# =================================================================================
# Existing HTML Serving Routes
# =================================================================================
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


if __name__ == '__main__':
    logging.info("Starting Flask application in local development mode.")
    app.run(debug=True, host='0.0.0.0', port=os.getenv('PORT', 8080))
