import os
import json
import logging
from flask import Flask, request, render_template, jsonify
from redis import Redis # Import Redis client
from rq import Queue, get_current_job # Import RQ Queue functionality

# Configure logging for better visibility in Render logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# --- Redis Queue Setup ---
# Get Redis URL from environment variable
redis_url = os.environ.get('REDIS_URL')
if not redis_url:
    logging.error("REDIS_URL environment variable not set. Cannot connect to Redis.")
    raise ValueError("REDIS_URL environment variable not set. Please configure it on Render.")

redis_conn = Redis.from_url(redis_url) # Establish connection to Redis
q = Queue(connection=redis_conn) # Create an RQ Queue instance (default queue name 'default')

# --- Flask Routes ---
@app.route('/')
def index():
    # Initial page with the form. No data is displayed initially as it's fetched asynchronously.
    return render_template('index.html', data=None, message=None)

@app.route('/get_stock_data', methods=['POST'])
def handle_stock_request():
    symbol = request.form['symbol'].upper()
    logging.info(f"Received request for stock: {symbol}. Enqueuing scraping job.")

    try:
        # Enqueue the scraping job to the Redis Queue.
        # The 'worker.scrape_and_save_to_sheets' string tells RQ:
        # "Look for a function named 'scrape_and_save_to_sheets' in a module named 'worker.py'"
        # 'symbol' is the argument passed to that function.
        # 'job_timeout' is crucial: give Selenium enough time, e.g., 10 minutes (600 seconds)
        job = q.enqueue('worker.scrape_and_save_to_sheets', symbol, job_timeout=600) 
        
        logging.info(f"Job for {symbol} enqueued with ID: {job.id}")
        
        # Immediately return a response to the user. The browser won't wait for the scrape to finish.
        return render_template('index.html', 
                               message=f"Scraping job for {symbol} submitted. Job ID: {job.id}. "
                                        "Please check your Google Sheet for updates or refresh this page later.",
                               job_id=job.id)
    except Exception as e:
        logging.error(f"Failed to enqueue job for {symbol}: {e}")
        return render_template('index.html', data=f"Failed to submit scraping job: {e}")

# Optional: Endpoint to check job status (useful for frontend polling)
@app.route('/status/<job_id>')
def job_status(job_id):
    job = q.fetch_job(job_id) # Fetch the job object by its ID
    if job:
        response = {
            'id': job.id,
            'status': job.get_status(), # 'queued', 'started', 'finished', 'failed'
            'result': job.result if job.is_finished else None, # This would be the return value of scrape_and_save_to_sheets
            'exc_info': job.exc_info # Detailed error info if the job failed
        }
    else:
        response = {'status': 'Job not found', 'id': job_id}
    logging.info(f"Status check for job {job_id}: {response['status']}")
    return jsonify(response)

# To display the *latest* data on the page directly, you would add logic here
# to read from Google Sheets using get_gspread_client() and then pass that data
# to the render_template on the '/' route or a new '/latest_data' route.
# For simplicity, we are currently telling the user to check Google Sheets.

if __name__ == '__main__':
    # When running locally: make sure Redis server is running (e.g., via Docker)
    # docker run -p 6379:6379 redis
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))
