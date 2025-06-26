import os
import logging
from flask import Flask, request, render_template, jsonify, session
import requests # Import the requests library to send HTTP requests

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
    # For a deployed app, you might want a more graceful failure or a setup guide.
    # For now, it will log the error and subsequent calls to the local processor will also log errors.

@app.route('/')
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
    Renders the data.html page.
    In a real application, this page would fetch or retrieve the processed stock data
    from another backend endpoint or a persistent storage (e.g., Firestore).
    For this example, data.html has simulated data as discussed previously.
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

if __name__ == '__main__':
    # When running locally, set a placeholder for LOCAL_PROCESSOR_URL
    # For example, if your local processor runs on port 8000
    os.environ['LOCAL_PROCESSOR_URL'] = 'http://127.0.0.1:8000'
    # Remember to set the actual ngrok/public URL in Render's environment variables
    app.run(debug=True, host='0.0.0.0', port=5000)

