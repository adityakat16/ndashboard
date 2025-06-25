import os
import logging
from flask import Flask, request, render_template, jsonify
import requests # Import the requests library to send HTTP requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# --- IMPORTANT: Environment Variable for Local Processor URL ---
# This will be set on Render's dashboard for your Web Service
LOCAL_PROCESSOR_URL = os.environ.get(' https://c382-2401-4900-4e59-93ce-fcea-48c-4413-ba5b.ngrok-free.app')
if not LOCAL_PROCESSOR_URL:
    logging.error("LOCAL_PROCESSOR_URL environment variable not set. Local processing will fail.")
    # In a production app, you might raise an error or redirect to an error page.
    # For now, we'll return an error message to the user.
    # It's good practice to ensure this is set during deployment.
    pass # Allow the app to run but handle the error in the route

@app.route('/')
def index():
    # This renders your main HTML form
    return render_template('index.html', data=None, message=None)

@app.route('/get_stock_data', methods=['POST'])
def handle_stock_request():
    symbol = request.form['symbol'].upper()
    logging.info(f"Received request for stock: {symbol} on Render. Forwarding to local processor.")

    if not LOCAL_PROCESSOR_URL:
        # Handle case where environment variable is not set
        logging.error("LOCAL_PROCESSOR_URL is not set on Render. Cannot forward request.")
        return render_template('index.html', message="Error: Local processor URL is not configured on the server. Please contact support.", data=None)

    try:
        # Send the stock symbol to your local Flask app via ngrok
        # Using timeout to ensure Render's app doesn't hang indefinitely if local server is slow to respond
        response = requests.post(
            f"{LOCAL_PROCESSOR_URL}/process_stock",
            json={'symbol': symbol},
            timeout=30 # Render's request timeout is 15s, but this is an OUTGOING request, give it a bit more
        )
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

        result = response.json()
        if result.get('status') == 'success':
            message = f"Scraping request for {symbol} sent to local machine. Data will be updated in Google Sheets."
            logging.info(f"Successfully forwarded request for {symbol} to local processor.")
        else:
            message = f"Warning: Local processor reported an issue for {symbol}: {result.get('message', 'Unknown issue.')}"
            logging.warning(f"Local processor returned warning for {symbol}: {result.get('message')}")

        # Return a message to the user immediately, as scraping happens asynchronously on local machine
        return render_template('index.html', message=message, data=None)

    except requests.exceptions.Timeout:
        logging.error(f"Timeout while trying to connect to local processor for {symbol}. Is it running and ngrok active?")
        return render_template('index.html', message="Failed to connect to local machine (timeout). Please ensure your local setup is running.", data=None)
    except requests.exceptions.ConnectionError:
        logging.error(f"Connection error to local processor for {symbol}. Is your ngrok URL correct and local server running?")
        return render_template('index.html', message="Failed to connect to local machine. Please check your local setup.", data=None)
    except requests.exceptions.RequestException as e:
        logging.error(f"General error forwarding request for {symbol} to local processor: {e}", exc_info=True)
        return render_template('index.html', message=f"An error occurred while sending request to local machine: {e}", data=None)
    except Exception as e:
        logging.error(f"An unexpected error occurred in app.py during request handling: {e}", exc_info=True)
        return render_template('index.html', message=f"An unexpected error occurred: {e}", data=None)

if __name__ == '__main__':
    app.run(debug=True)
