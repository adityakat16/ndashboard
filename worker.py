import os
import json
import logging
from datetime import datetime

from redis import Redis
from rq import Worker, Queue, Connection

# IMPORTANT: Import your scraping function from sele.py
from sele import run_scraper 

# Import gspread and oauth2client for Google Sheets interaction
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configure logging for the worker, so you can see its progress in Render logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Google Sheets Authentication and Helper Functions ---
# These functions are identical to what you had in app.py for Google Sheets,
# but they are now solely used by the worker.
def get_gspread_client():
    creds_json_str = os.environ.get('GSPREAD_SERVICE_ACCOUNT_CREDENTIALS')
    if not creds_json_str:
        logging.error("GSPREAD_SERVICE_ACCOUNT_CREDENTIALS environment variable not set in worker.")
        raise ValueError("GSPREAD_SERVICE_ACCOUNT_CREDENTIALS environment variable not set.")

    try:
        creds_info = json.loads(creds_json_str)
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        logging.info("Google Sheets client authorized successfully in worker.")
        return client
    except Exception as e:
        logging.error(f"Error authenticating with Google Sheets API in worker: {e}", exc_info=True)
        raise

def update_worksheet_with_data(spreadsheet_name, worksheet_name, headers, data_rows):
    """
    Clears the specified worksheet, then writes headers and new data rows.
    data_rows should be a list of lists (where each inner list is a row).
    """
    try:
        client = get_gspread_client()
        spreadsheet = client.open(spreadsheet_name)
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        logging.info(f"Clearing worksheet '{worksheet_name}' in '{spreadsheet_name}'...")
        worksheet.clear() 

        logging.info(f"Writing headers to '{worksheet_name}'...")
        worksheet.append_row(headers) 

        if data_rows:
            logging.info(f"Appending {len(data_rows)} data rows to '{worksheet_name}'...")
            worksheet.append_rows(data_rows) 
        else:
            logging.info(f"No data rows to append to '{worksheet_name}'.")

        logging.info(f"Worksheet '{worksheet_name}' updated successfully by worker.")
    except Exception as e:
        logging.error(f"Error updating Google Sheet '{spreadsheet_name}' (worksheet '{worksheet_name}') in worker: {e}", exc_info=True)
        raise

# --- The main task function that RQ will execute ---
def scrape_and_save_to_sheets(symbol):
    """
    This function performs the actual web scraping and saves data to Google Sheets.
    It runs in the background worker process.
    """
    logging.info(f"Worker: Started scraping job for symbol: {symbol}")
    
    # Define the name of your Google Spreadsheet
    GOOGLE_SHEET_NAME = "StockData" # <--- IMPORTANT: Change this to your actual Google Sheet name

    try:
        scraped_data = run_scraper(symbol) # Call your core scraping logic from sele.py

        if scraped_data:
            logging.info(f"Worker: Scraped data for {symbol} successfully. Preparing to write to Google Sheets.")
            
            current_time_utc = datetime.utcnow().isoformat() + 'Z'

            # 1. Overall Ratios Data (Sheet: "Overall")
            overall_headers = ["Symbol", "Timestamp (UTC)", "PROMOTERS", "FII", "DII", "PUBLIC", "CMP", "F_HIGH", 
                               "F_LOW", "HiLoPer", "PB", "pe_1yr", "pe_3yr", "pe_5yr", "pe_10yr", "DY"]
            overall_data_row = [
                symbol,
                current_time_utc,
                str(scraped_data.get("PROMOTERS", "N/A")),
                str(scraped_data.get("FII", "N/A")),
                str(scraped_data.get("DII", "N/A")),
                str(scraped_data.get("PUBLIC", "N/A")),
                str(scraped_data.get("CMP", "N/A")),
                str(scraped_data.get("F_HIGH", "N/A")),
                str(scraped_data.get("F_LOW", "N/A")),
                str(scraped_data.get("HiLoPer", "N/A")),
                str(scraped_data.get("PB", "N/A")),
                str(scraped_data.get("pe_1yr", "N/A")),
                str(scraped_data.get("pe_3yr", "N/A")),
                str(scraped_data.get("pe_5yr", "N/A")),
                str(scraped_data.get("pe_10yr", "N/A")),
                str(scraped_data.get("DY", "N/A"))
            ]
            update_worksheet_with_data(GOOGLE_SHEET_NAME, "Overall", overall_headers, [overall_data_row])
            logging.info("Worker: Overall data written to Google Sheet.")

            # 2. Annual Data (Sheet: "Annual Data")
            # Adjust headers to match years/columns in your Screener.in output
            annual_headers = ["Symbol", "Timestamp (UTC)", "Metric", "Yr-1", "Yr-2", "Yr-3", "Yr-4", "Yr-5"] # Example years
            annual_rows = []
            annual_rows.append([symbol, current_time_utc, "Sales"] + [str(v) for v in scraped_data.get("asales", [])])
            annual_rows.append([symbol, current_time_utc, "Other Income"] + [str(v) for v in scraped_data.get("aOther_Income", [])])
            annual_rows.append([symbol, current_time_utc, "Total Revenue"] + [str(v) for v in scraped_data.get("aTotal_Revenue", [])])
            annual_rows.append([symbol, current_time_utc, "Revenue Growth"] + [str(v) for v in scraped_data.get("aRevenue_Growth", [])])
            # Add other annual metrics similarly
            
            update_worksheet_with_data(GOOGLE_SHEET_NAME, "Annual Data", annual_headers, annual_rows)
            logging.info("Worker: Annual data written to Google Sheet.")

            # 3. Quarterly Data (Sheet: "Quarterly Data")
            # Adjust headers to match quarters/columns
            quarterly_headers = ["Symbol", "Timestamp (UTC)", "Metric", "Q1", "Q2", "Q3", "Q4"] # Example quarters
            quarterly_rows = []
            quarterly_rows.append([symbol, current_time_utc, "Sales"] + [str(v) for v in scraped_data.get("qsales", [])])
            # Add other quarterly metrics similarly

            update_worksheet_with_data(GOOGLE_SHEET_NAME, "Quarterly Data", quarterly_headers, quarterly_rows)
            logging.info("Worker: Quarterly data written to Google Sheet.")

            logging.info(f"Worker: Successfully completed job for {symbol}.")
            return f"Success: Data for {symbol} saved to Google Sheets." # This message goes into job.result

        else:
            logging.warning(f"Worker: No data scraped for {symbol}. Job completed without data.")
            return f"Warning: No data for {symbol}."

    except Exception as e:
        logging.error(f"Worker: Critical error during scraping or saving for {symbol}: {e}", exc_info=True)
        # Re-raise the exception so RQ marks the job as 'failed' and logs the traceback
        raise 

# --- Worker Entry Point ---
if __name__ == '__main__':
    logging.info("RQ Worker process starting...")
    redis_url = os.environ.get('REDIS_URL')
    if not redis_url:
        logging.error("REDIS_URL environment variable not set for worker startup. Exiting.")
        raise ValueError("REDIS_URL environment variable not set for worker startup.")
        
    # Connect to Redis and start the worker
    with Connection(Redis.from_url(redis_url)):
        # Listen to the 'default' queue. If you use multiple queues, list them here.
        worker = Worker(map(Queue, ['default'])) 
        logging.info("RQ Worker connected to Redis. Starting to listen for jobs.")
        worker.work() # This call blocks and makes the worker listen for jobs indefinitely
