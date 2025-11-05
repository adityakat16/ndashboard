import os
import json
import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify

# Import your scraper module (ensure selelh.py is in the same directory)
from selelh import run_scraper
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- IMPORTANT: Configure logging first to see all messages ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)


current_year = (datetime.now().year)%100
nyr=current_year+1
nnyr=nyr+1


# --- CONSTANT: Define the name of your local credentials file ---
# Make sure this matches the actual name of your JSON key file (e.g., 'service_key.json' or 'credentials.json')
LOCAL_CREDENTIALS_FILE = 'credentials.json' # <<<--- IMPORTANT: ADJUST THIS IF YOUR FILE IS NAMED DIFFERENTLY (e.g., 'service_key.json')

# --- Google Sheets Authentication Function (UPDATED WITH LOCAL FALLBACK) ---
def get_gspread_client():
    """
    Authenticates with Google Sheets.
    First tries to use GSPREAD_SERVICE_ACCOUNT_CREDENTIALS environment variable.
    If not set, falls back to loading from a local JSON file specified by LOCAL_CREDENTIALS_FILE.
    """
    credentials_json_str = os.getenv("GSPREAD_SERVICE_ACCOUNT_CREDENTIALS")

    if credentials_json_str:
        # If environment variable is set, use it (this is for production/Render)
        logging.info("Using GSPREAD_SERVICE_ACCOUNT_CREDENTIALS from environment variable.")
        try:
            creds_info = json.loads(credentials_json_str)
            # gspread.service_account_from_dict is preferred for JSON string input
            return gspread.service_account_from_dict(creds_info)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from GSPREAD_SERVICE_ACCOUNT_CREDENTIALS environment variable: {e}")
            raise ValueError(f"Invalid JSON in GSPREAD_SERVICE_ACCOUNT_CREDENTIALS environment variable: {e}")
        except Exception as e:
            logging.error(f"Unexpected error with GSPREAD_SERVICE_ACCOUNT_CREDENTIALS environment variable: {e}")
            raise
    else:
        # Fallback for local development: Try to load from a local file
        logging.warning("GSPREAD_SERVICE_ACCOUNT_CREDENTIALS environment variable not set. Attempting to load from local file.")
        try:
            # Construct the full path to the credentials file
            script_dir = os.path.dirname(__file__)
            credentials_path = os.path.join(script_dir, LOCAL_CREDENTIALS_FILE)

            if not os.path.exists(credentials_path):
                logging.error(f"Local credentials file NOT FOUND at: {credentials_path}")
                raise FileNotFoundError(f"Local credentials file '{LOCAL_CREDENTIALS_FILE}' not found. Please set the environment variable or create this file.")

            logging.info(f"Loading credentials from local file: {credentials_path}")
            # gspread.service_account is preferred for file path input
            return gspread.service_account(filename=credentials_path)

        except FileNotFoundError as e:
            logging.error(f"Error: Local credentials file missing: {e}")
            raise ValueError("GSPREAD_SERVICE_ACCOUNT_CREDENTIALS environment variable not set and local credentials file not found.")
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from local credentials file '{LOCAL_CREDENTIALS_FILE}': {e}")
            raise ValueError(f"Invalid JSON in local credentials file '{LOCAL_CREDENTIALS_FILE}'.")
        except Exception as e:
            logging.error(f"Unexpected error loading GSpread client from local file: {e}", exc_info=True)
            raise ValueError(f"GSpread client setup failed from local file: {e}")


def update_worksheet_with_data(spreadsheet_name, worksheet_name, headers, data_rows):
    """
    Updates a specific worksheet in a Google Sheet with provided headers and data rows.
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
            # gspread.append_rows expects a list of lists
            worksheet.append_rows(data_rows) 
        else:
            logging.info(f"No data rows to append to '{worksheet_name}'.")

        logging.info(f"Worksheet '{worksheet_name}' updated successfully by local_processor.")
    except Exception as e:
        logging.error(f"Error updating Google Sheet '{spreadsheet_name}' (worksheet '{worksheet_name}') in local_processor: {e}", exc_info=True)
        # Re-raise the exception so the caller (process_stock_request) can catch it
        raise


# --- Endpoint for Receiving Requests from Render ---
@app.route('/process_input', methods=['POST'])
def process_stock_request():
    """
    Receives a stock symbol from the Render app, scrapes data, and updates Google Sheets.
    """
    try:
        
        
        
        
        
        
        data = request.get_json() # Expect JSON payload from Render app
        logging.info(f"Local Processor: Received raw JSON data: {data}")

        if not data or 'stock_symbol' not in data:
            logging.error("Local Processor: Invalid JSON payload: 'symbol' key is missing or data is not JSON.")
            return jsonify({"status": "error", "message": "Invalid request: 'symbol' not found in JSON payload."}), 400

        symbol = data.get('stock_symbol').upper() # Extract and standardize the stock symbol

        logging.info(f"Local Processor: Processing request for stock: {symbol}")

        # --- IMPORTANT: Ensure this matches your actual Google Sheet name ---
        GOOGLE_SHEET_NAME = "Stock Database"

        scraped_data = run_scraper(symbol) # Execute the web scraping

        if scraped_data:
            logging.info(f"Local Processor: Scraped data for {symbol}. Preparing to write to Google Sheets.")
            # Fix for DeprecationWarning: datetime.datetime.utcnow()
            current_time_utc = datetime.now(timezone.utc).isoformat() 
            stock_name=scraped_data.get("STOCK","NA")
            # 1. Overall Ratios Data
            overall_data_rows=[]
            overall_data_rows.append(['CMP', str(scraped_data.get("CMP", "N/A"))])
            overall_data_rows.append(['52 H', str(scraped_data.get("F_HIGH", "N/A"))])
            overall_data_rows.append(['52 L', str(scraped_data.get("F_LOW", "N/A"))])
            overall_data_rows.append(['CMP %', str(scraped_data.get("HiLoPer", "N/A"))])
            overall_data_rows.append(['MCAP/Sales', str(scraped_data.get("McapSales", "N/A"))])
            overall_data_rows.append(['PROMOTERS %', str(scraped_data.get("PROMOTERS", "N/A"))])
            overall_data_rows.append(['FII %', str(scraped_data.get("FII", "N/A"))])
            overall_data_rows.append(['DII %', str(scraped_data.get("DII", "N/A"))])
            overall_data_rows.append(['PUBLIC %', str(scraped_data.get("PUBLIC", "N/A"))])            
            overall_data_rows.append(['PB', str(scraped_data.get("PB", "N/A"))])
            overall_data_rows.append(['PE', str(scraped_data.get("peCur", "N/A"))])
            overall_data_rows.append(['PE 3yr', str(scraped_data.get("pe_3yr", "N/A"))])
            overall_data_rows.append(['PE 5yr', str(scraped_data.get("pe_5yr", "N/A"))])
            overall_data_rows.append(['PE 10yr', str(scraped_data.get("pe_10yr", "N/A"))])
            overall_data_rows.append(['PE Industry', "N/A"])
            overall_data_rows.append(['Dividend Yield', str(scraped_data.get("DY", "N/A"))])
                        
            update_worksheet_with_data(GOOGLE_SHEET_NAME, "Overall",[],overall_data_rows)
            logging.info("Local Processor: Overall data written to Google Sheet.")

            # 2. Annual Data
            anperiods=scraped_data.get("aPeriods",[])
            annual_headers = ["Annual"] + anperiods
            annual_rows = []
            annual_rows.append(["Sales"] + [str(v) for v in scraped_data.get("asales", [])])
            annual_rows.append(["Other Income"] + [str(v) for v in scraped_data.get("aOther_Income", [])])
            annual_rows.append(["Total Revenue"] + [str(v) for v in scraped_data.get("aTotal_Revenue", [])])
            annual_rows.append(["Revenue Growth"] + [str(v) for v in scraped_data.get("aRevenue_Growth", [])])
            annual_rows.append(["Net Profit"] + [str(v) for v in scraped_data.get("aNet_Profit", [])])
            annual_rows.append(["Net Profit Margin"] + [str(v) for v in scraped_data.get("aNet_Profit_Margin", [])])
            annual_rows.append(["EPS"] + [str(v) for v in scraped_data.get("aEPS", [])])
            annual_rows.append(["EPS GROWTH"] + [str(v) for v in scraped_data.get("aEPS_Growth", [])])
            annual_rows.append(["Dividend Payout %"] + [str(v) for v in scraped_data.get("aDividend_Payout", [])])
            annual_rows.append(["Promoter %"] + [str(v) for v in scraped_data.get("aPromoter", [])])
            annual_rows.append(["FII %"] + [str(v) for v in scraped_data.get("aFII", [])])
            annual_rows.append(["DII %"] + [str(v) for v in scraped_data.get("aDII", [])])
            update_worksheet_with_data(GOOGLE_SHEET_NAME, "Annual Data", annual_headers, annual_rows)
            logging.info("Local Processor: Annual data written to Google Sheet.")

            # 3. Quarterly Data
            quperiods=scraped_data.get("qPeriods",[])
            quarterly_headers = [ "Quarterly"] + quperiods
            quarterly_rows = []
            quarterly_rows.append(["Sales"] + [str(v) for v in scraped_data.get("qsales", [])])
            quarterly_rows.append(["Other Income"] + [str(v) for v in scraped_data.get("qOther_Income", [])])
            quarterly_rows.append(["Total Revenue"] + [str(v) for v in scraped_data.get("qTotal_Revenue", [])])
            quarterly_rows.append(["RG%"] + [str(v) for v in scraped_data.get("qRevenue_Growth", [])])
            quarterly_rows.append(["Net Profit"] + [str(v) for v in scraped_data.get("qNet_Profit", [])])
            quarterly_rows.append(["Net Profit Margin"] + [str(v) for v in scraped_data.get("qNet_Profit_Margin", [])])
            quarterly_rows.append(["EPS"] + [str(v) for v in scraped_data.get("qEPS", [])])
            quarterly_rows.append(["EPS GROWTH"] + [str(v) for v in scraped_data.get("qEPS_Growth", [])])
            quarterly_rows.append(["Promoter %"] + [str(v) for v in scraped_data.get("qPromoter", [])])
            quarterly_rows.append(["FII %"] + [str(v) for v in scraped_data.get("qFII", [])])
            quarterly_rows.append(["DII %"] + [str(v) for v in scraped_data.get("qDII", [])])
            update_worksheet_with_data(GOOGLE_SHEET_NAME, "Quarterly Data", quarterly_headers, quarterly_rows)
            logging.info("Local Processor: Quarterly data written to Google Sheet.")
            
            # 4. stock symbol
            stock_row = [[stock_name]]  
            update_worksheet_with_data(GOOGLE_SHEET_NAME, "Stock_Symbol", [], stock_row)
            logging.info("Local Processor: Stock symbol written to Google Sheet.")
            
            #5 Projected Data
            proj_data_rows=[]
            proj_data_rows.append(['Avg Q EPS Growth', str(scraped_data.get("AvgEPSG", "N/A"))])
            proj_data_rows.append(['Yearly EPS Growth', str(scraped_data.get("YrEPSG", "N/A"))])
            proj_data_rows.append([f'EPS @ MAR {nyr}', str(scraped_data.get("EPSnyr", "N/A"))])
            proj_data_rows.append(['PE for Calculation', str(scraped_data.get("PEcal", "N/A"))])
            proj_data_rows.append([f'Stock Price @ Apr {nyr}', str(scraped_data.get("Pro_Priceny", "N/A"))])
            proj_data_rows.append([f'Stock Price @ Apr {nnyr}', str(scraped_data.get("Pro_Pricenny", "N/A"))])
            
            update_worksheet_with_data(GOOGLE_SHEET_NAME, "Projections Data",[],proj_data_rows)
            logging.info("Local Processor: Projections data written to Google Sheet.")

            logging.info(f"Local Processor: Successfully completed job for {symbol}.")
            # Return success response to the Render app
            return jsonify({"status": "success", "message": f"Data for {symbol} saved to Google Sheets."}), 200
        else:
            logging.warning(f"Local Processor: No data scraped for {symbol}. Job completed without data.")
            # Return warning response to the Render app
            return jsonify({"status": "warning", "message": f"No data scraped for {symbol}."}), 200
        
    except Exception as e:
        logging.error(f"Local Processor: Critical error during scraping or saving for {symbol}: {e}", exc_info=True)
        # Return error response to the Render app
        return jsonify({"status": "error", "message": f"An unexpected error occurred during processing: {e}"}), 500

if __name__ == '__main__':
    print("Starting local Flask server on port 5000...")
    print(f"Remember to place your service account JSON file as '{LOCAL_CREDENTIALS_FILE}' in the same directory.")
    print("Alternatively, set the GSPREAD_SERVICE_ACCOUNT_CREDENTIALS environment variable.")
    print("Also, ensure ngrok is running and forwarding to this port (80).")
    app.run(port=80, debug=True) # Run Flask app on port 80
    
