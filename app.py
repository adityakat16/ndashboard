import os
import logging
from flask import Flask, request, render_template, jsonify
import requests # Import the requests library to send HTTP requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# --- IMPORTANT: Environment Variable for Local Processor URL ---
# You will set this on Render's dashboard for your Web Service
LOCAL_PROCESSOR_URL = os.environ.get('LOCAL_PROCESSOR_URL')
if not LOCAL_PROCESSOR_URL:
    logging.error("LOCAL_PROCESSOR_URL environment variable not set. Local processing will fail.")
    # Raise an error or set a default error message
    raise ValueError("LOCAL_PROCESSOR_URL environment variable not set. Please configure it on Render.")


@app.route('/')
def index():
    return render_template('index.html', data=None, message=None)

@app.route('/get_stock_data', methods=['POST'])
def handle_stock_request():
    symbol = request.form['symbol'].upper()
    logging.info(f"Received request for stock: {symbol}. Forwarding to local processor.")

    if not LOCAL_PROCESSOR_URL:
        return render_template('index.html', message="Error: Local processor URL not configured.", data=None)

    try:
        # Send the stock symbol to your local Flask app via ngrok
        response = requests.post(
            f"{LOCAL_PROCESSOR_URL}/process_stock",
            json={'symbol': symbol},
            timeout=30 # Give it more time, as local scraping can be slow. Render's own timeout still applies.
        )
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

        result = response.json()
        if result.get('status') == 'success':
            message = f"Scraping request for {symbol} sent to local machine. {result.get('message', '')}"
            logging.info(f"Successfully forwarded request for {symbol} to local processor.")
        else:
            message = f"Warning processing {symbol} locally: {result.get('message', 'Unknown issue.')}"
            logging.warning(f"Local processor returned warning for {symbol}: {result.get('message')}")

        return render_template('index.html', message=message, data=None)

    except requests.exceptions.RequestException as e:
        logging.error(f"Error forwarding request for {symbol} to local processor: {e}", exc_info=True)
        return render_template('index.html', message=f"Failed to send request to local machine: {e}", data=None)
    except Exception as e:
        logging.error(f"An unexpected error occurred in app.py: {e}", exc_info=True)
        return render_template('index.html', message=f"An unexpected error occurred: {e}", data=None)

if __name__ == '__main__':
    app.run(debug=True)
