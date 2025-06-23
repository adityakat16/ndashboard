# app.py (Reverted to synchronous)
import os
import json
import logging
from flask import Flask, request, render_template, jsonify
from datetime import datetime

from sele import run_scraper # Re-import your scraper here
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# --- Google Sheets Authentication and Helper Functions (BACK IN APP.PY) ---
def get_gspread_client():
    creds_json_str = os.environ.get('GSPREAD_SERVICE_ACCOUNT_CREDENTIALS')
    if not creds_json_str:
        logging.error("GSPREAD_SERVICE_ACCOUNT_CREDENTIALS environment variable not set.")
        raise ValueError("GSPREAD_SERVICE_ACCOUNT_CREDENTIALS environment variable not set.")

    try:
        creds_info = json.loads(creds_json_str)
        scope = ['https://sheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        logging.info("Google Sheets client authorized successfully.")
        return client
    except Exception as e:
        logging.error(f"Error authenticating with Google Sheets API: {e}")
        raise

def update_worksheet_with_data(spreadsheet_name, worksheet_name, headers, data_rows):
    # ... (same as before, but called by app.py) ...
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

        logging.info(f"Worksheet '{worksheet_name}' updated successfully.")
    except Exception as e:
        logging.error(f"Error updating Google Sheet '{spreadsheet_name}' (worksheet '{worksheet_name}'): {e}")
        raise

# --- Flask Routes ---
@app.route('/')
def index():
    # Maybe show some static message or last known data if you read from sheet
    return render_template('index.html', data=None, message=None)

@app.route('/get_stock_data', methods=['POST'])
def handle_stock_request():
    symbol = request.form['symbol'].upper()
    logging.info(f"Received synchronous request for stock: {symbol}.")

    GOOGLE_SHEET_NAME = "StockData" # <--- IMPORTANT: Change this to your actual Google Sheet name

    try:
        # DIRECTLY CALL THE SCRAPER (This is where timeouts will happen)
        scraped_data = run_scraper(symbol)

        if scraped_data:
            logging.info(f"Scraped data for {symbol} synchronously. Writing to Google Sheets.")
            current_time_utc = datetime.utcnow().isoformat() + 'Z'

            # 1. Overall Ratios Data
            overall_headers = ["Symbol", "Timestamp (UTC)", "PROMOTERS", "FII", "DII", "PUBLIC", "CMP", "F_HIGH", 
                            "F_LOW", "HiLoPer", "PB", "pe_1yr", "pe_3yr", "pe_5yr", "pe_10yr", "DY"]
            overall_data_row = [
                symbol, current_time_utc,
                str(scraped_data.get("PROMOTERS", "N/A")), str(scraped_data.get("FII", "N/A")),
                str(scraped_data.get("DII", "N/A")), str(scraped_data.get("PUBLIC", "N/A")),
                str(scraped_data.get("CMP", "N/A")), str(scraped_data.get("F_HIGH", "N/A")),
                str(scraped_data.get("F_LOW", "N/A")), str(scraped_data.get("HiLoPer", "N/A")),
                str(scraped_data.get("PB", "N/A")), str(scraped_data.get("pe_1yr", "N/A")),
                str(scraped_data.get("pe_3yr", "N/A")), str(scraped_data.get("pe_5yr", "N/A")),
                str(scraped_data.get("pe_10yr", "N/A")), str(scraped_data.get("DY", "N/A"))
            ]
            update_worksheet_with_data(GOOGLE_SHEET_NAME, "Overall", overall_headers, [overall_data_row])

            # 2. Annual Data
            annual_headers = ["Symbol", "Timestamp (UTC)", "Metric", "Yr-1", "Yr-2", "Yr-3", "Yr-4", "Yr-5"]
            annual_rows = []
            annual_rows.append([symbol, current_time_utc, "Sales"] + [str(v) for v in scraped_data.get("asales", [])])
            annual_rows.append([symbol, current_time_utc, "Other Income"] + [str(v) for v in scraped_data.get("aOther_Income", [])])
            annual_rows.append([symbol, current_time_utc, "Total Revenue"] + [str(v) for v in scraped_data.get("aTotal_Revenue", [])])
            annual_rows.append([symbol, current_time_utc, "Revenue Growth"] + [str(v) for v in scraped_data.get("aRevenue_Growth", [])])
            update_worksheet_with_data(GOOGLE_SHEET_NAME, "Annual Data", annual_headers, annual_rows)

            # 3. Quarterly Data
            quarterly_headers = ["Symbol", "Timestamp (UTC)", "Metric", "Q1", "Q2", "Q3", "Q4"]
            quarterly_rows = []
            quarterly_rows.append([symbol, current_time_utc, "Sales"] + [str(v) for v in scraped_data.get("qsales", [])])
            update_worksheet_with_data(GOOGLE_SHEET_NAME, "Quarterly Data", quarterly_headers, quarterly_rows)

            logging.info(f"Finished synchronous scrape and save for {symbol}.")
            # Render the template with the *result* or a success message
            return render_template('index.html', data=f"Successfully scraped and saved data for {symbol}. Check your Google Sheet!", message="Data fetched!")
        else:
            logging.warning(f"No data scraped for {symbol} synchronously.")
            return render_template('index.html', data=f"Failed to retrieve stock data for {symbol}", message="Scraping failed!")

    except Exception as e:
        logging.error(f"Error during synchronous scraping for {symbol}: {e}", exc_info=True)
        return render_template('index.html', data=f"An error occurred: {e}", message="Error!")

if __name__ == '__main__':
    app.run(debug=True)
