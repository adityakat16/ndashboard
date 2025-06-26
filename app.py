import os
import logging
from flask import Flask, request, render_template, jsonify, session # session is imported but not used, can be removed if not needed later
import requests # Used for forwarding to local processor

# Google Sheets API imports
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json # Used to parse the service account JSON from environment variable

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
# Enable Flask sessions if you plan to store data temporarily across requests
# app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_super_secret_key_here')
# It's highly recommended to set this as an environment variable in production

# --- IMPORTANT: Environment Variable for Local Processor URL ---
# This will be set on Render's dashboard for your Web Service
LOCAL_PROCESSOR_URL = os.environ.get('LOCAL_PROCESSOR_URL')
if not LOCAL_PROCESSOR_URL:
    logging.error("LOCAL_PROCESSOR_URL environment variable not set. Local processing will fail.")

# --- Google Sheets API Setup ---
# Get the service account key JSON from environment variable
GOOGLE_CREDENTIALS_JSON = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')

# Define the scope for accessing Google Sheets.
# 'https://www.googleapis.com/auth/spreadsheets' allows read and write.
# If this app only reads, 'https://www.googleapis.com/auth/spreadsheets.readonly' is more secure.
# Since your local processor might also use this key to write, a broader scope might be needed for the key itself.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets'] # Use a scope that allows both read/write if your service account is used for writing too.

service = None # Initialize service as None
if GOOGLE_CREDENTIALS_JSON:
    try:
        info = json.loads(GOOGLE_CREDENTIALS_JSON)
        credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials)
        logging.info("Google Sheets API service initialized successfully on Render.")
    except Exception as e:
        logging.error(f"Failed to initialize Google Sheets API service on Render: {e}", exc_info=True)
else:
    logging.error("GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable not set on Render. Google Sheets API will not work.")


@app.route('/')
@app.route('/index.html')
def index():
    """
    Renders the main index.html page.
    This page sends stock symbol requests to the backend and then redirects.
    """
    return render_template('index.html')

@app.route('/loading.html')
def loading_page():
    """
    Renders the loading.html page.
    This page is shown after the user clicks 'Get Data' and while the backend processes.
    """
    return render_template('loading.html')

@app.route('/data.html')
def data_page():
    """
    Renders the data.html page. This page will then fetch data from /get_sheet_data_from_gsheets.
    """
    return render_template('data.html')

@app.route('/get_stock_data', methods=['POST'])
def handle_stock_request():
    """
    Handles the incoming POST request from index.html (sent via fetch API).
    Receives JSON data, logs it, and forwards it to the LOCAL_PROCESSOR_URL.
    Returns a JSON response to the frontend's fetch call.
    The frontend (index.html) is responsible for redirecting to loading.html immediately.
    """
    if not request.is_json:
        logging.error("Received non-JSON request to /get_stock_data.")
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400

    data = request.get_json()
    symbol = data.get('symbol')

    if not symbol:
        logging.error("Received JSON request without 'symbol' key.")
        return jsonify({"status": "error", "message": "Missing 'symbol' in request body"}), 400

    symbol = symbol.upper() # Ensure symbol is uppercase as per your original logic
    logging.info(f"Received request for stock: {symbol}. Forwarding to local processor.")

    if not LOCAL_PROCESSOR_URL:
        logging.error("LOCAL_PROCESSOR_URL is not set on Render. Cannot forward request.")
        return jsonify({
            "status": "error",
            "message": "Local processor URL is not configured on the server."
        }), 500

    try:
        # Send the stock symbol to your local Flask app via ngrok
        # The local processor is expected to handle the actual data fetching
        # and Google Sheets writing.
        response = requests.post(
            f"{LOCAL_PROCESSOR_URL}/process_stock",
            json={'symbol': symbol},
            timeout=30 # Increased timeout for external request
        )
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

        result = response.json()
        if result.get('status') == 'success':
            logging.info(f"Successfully forwarded request for {symbol} to local processor. Local processor message: {result.get('message', 'No message.')}")
            # Return a success JSON to the fetch call on the frontend
            return jsonify({
                "status": "success",
                "message": f"Scraping request for {symbol} sent to local machine. Data will be updated in Google Sheets."
            }), 200
        else:
            logging.warning(f"Local processor reported an issue for {symbol}: {result.get('message', 'Unknown issue.')}")
            # Return a warning/error JSON to the fetch call on the frontend
            return jsonify({
                "status": "warning",
                "message": f"Local processor reported an issue: {result.get('message', 'Unknown issue.')}"
            }), 200 # Still return 200 if the forwarding itself was successful, but the *local processing* had a warning.

    except requests.exceptions.Timeout:
        logging.error(f"Timeout while trying to connect to local processor for {symbol}. Is it running and ngrok active?")
        return jsonify({
            "status": "error",
            "message": "Failed to connect to local machine (timeout). Please ensure your local setup is running."
        }), 504 # Gateway Timeout
    except requests.exceptions.ConnectionError:
        logging.error(f"Connection error to local processor for {symbol}. Is your ngrok URL correct and local server running?")
        return jsonify({
            "status": "error",
            "message": "Failed to connect to local machine. Please check your local setup and ngrok URL."
        }), 503 # Service Unavailable
    except requests.exceptions.RequestException as e:
        logging.error(f"General HTTP error forwarding request for {symbol} to local processor: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"An HTTP error occurred while sending request to local machine: {e}"
        }), 500
    except Exception as e:
        logging.error(f"An unexpected error occurred in app.py during request handling: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"An unexpected server error occurred: {e}"
        }), 500

# --- NEW: Route to get data from Google Sheets ---
@app.route('/get_sheet_data_from_gsheets', methods=['GET']) # Using a distinct name
def get_sheet_data_from_gsheets():
    """
    Fetches data directly from Google Sheets using the Sheets API.
    This endpoint is called by data.html.
    """
    global service # Use global service object
    if not service:
        logging.error("Google Sheets API service not initialized. Cannot fetch data.")
        return jsonify({"status": "error", "message": "Google Sheets API not configured on server."}), 500

    # --- Configuration for your Google Sheet ---
    # Replace with your actual Spreadsheet ID and Range
    # You can find the Spreadsheet ID in the URL: https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit
    SPREADSHEET_ID = 'YOUR_GOOGLE_SHEET_ID_HERE' # <--- IMPORTANT: REPLACE THIS
    # The range to read. Example: 'Sheet1!A1:E10' or just 'Sheet1' for all data on that sheet.
    RANGE_NAME = 'Sheet1!A1:Z' # Reads from A1 to Z (all rows in Z) of Sheet1, adjust as needed

    try:
        # Call the Sheets API to get values
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            majorDimension='ROWS' # Get data row by row
        ).execute()
        values = result.get('values', [])

        if not values:
            logging.info("No data found in the specified Google Sheet range.")
            return jsonify({"status": "ready", "data": [], "message": "No data found."}), 200

        # Log and return the data
        logging.info(f"Successfully fetched {len(values)} rows from Google Sheet.")
        # The Sheets API returns data as a list of lists. The first inner list is usually the header.
        return jsonify({"status": "ready", "data": values, "message": "Data fetched successfully!"}), 200

    except Exception as e:
        logging.error(f"Error fetching data from Google Sheet: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Failed to fetch data from Google Sheet: {str(e)}"}), 500


if __name__ == '__main__':
    # When running locally, set a placeholder for LOCAL_PROCESSOR_URL
    os.environ['LOCAL_PROCESSOR_URL'] = 'http://127.0.0.1:8000' # Example for your local processor
    # For local testing, load GOOGLE_APPLICATION_CREDENTIALS_JSON from a file if environment variable is not set
    # This block is for local development only. Render will use its environment variables.
    if not GOOGLE_CREDENTIALS_JSON:
        try:
            # Assumes service_account_key.json is in the same directory as app.py
            with open('service_account_key.json', 'r') as f:
                local_creds_json = f.read()
                # Set env var for consistency, or just use `info` directly
                # os.environ['GOOGLE_APPLICATION_CREDENTIALS_JSON'] = local_creds_json
                logging.info("Attempting to load GOOGLE_APPLICATION_CREDENTIALS_JSON from local file for development.")

            local_info = json.loads(local_creds_json)
            local_credentials = service_account.Credentials.from_service_account_info(local_info, scopes=SCOPES)
            service = build('sheets', 'v4', credentials=local_credentials)
            logging.info("Google Sheets API service initialized locally.")
        except FileNotFoundError:
            logging.warning("service_account_key.json not found locally. Google Sheets API will not work in local development without it.")
        except Exception as e:
            logging.error(f"Error loading local service account key or initializing Sheets API locally: {e}", exc_info=True)
    app.run(debug=True, host='0.0.0.0', port=5000) # Your Render app's local port
