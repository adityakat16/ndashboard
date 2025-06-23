from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import os
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# --- Database Setup (Highly Recommended for Data Persistence) ---
# Replace with your actual database connection code if using a database
# Example using PostgreSQL (requires psycopg2-binary in requirements.txt and DATABASE_URL env var on Render)
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn
    except Exception as e:
        logging.error(f"Error connecting to database: {e}")
        return None

def setup_database():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS stock_data (
                    symbol VARCHAR(10) PRIMARY KEY,
                    company_name TEXT,
                    cmp TEXT,
                    pe_ratio TEXT,
                    market_cap TEXT,
                    roce TEXT,
                    roe TEXT,
                    div_yield TEXT,
                    sales_growth TEXT,
                    pledged_perc TEXT,
                    cash_equiv TEXT,
                    debt_equiv TEXT,
                    interest_cov TEXT,
                    reserves TEXT,
                    face_value TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            cur.close()
            logging.info("Database table 'stock_data' ensured to exist.")
        except Exception as e:
            logging.error(f"Error setting up database: {e}")
        finally:
            conn.close()

def save_stock_data(data):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO stock_data (symbol, company_name, cmp, pe_ratio, market_cap, roce, roe, div_yield,
                                        sales_growth, pledged_perc, cash_equiv, debt_equiv, interest_cov,
                                        reserves, face_value, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (symbol) DO UPDATE SET
                    company_name = EXCLUDED.company_name,
                    cmp = EXCLUDED.cmp,
                    pe_ratio = EXCLUDED.pe_ratio,
                    market_cap = EXCLUDED.market_cap,
                    roce = EXCLUDED.roce,
                    roe = EXCLUDED.roe,
                    div_yield = EXCLUDED.div_yield,
                    sales_growth = EXCLUDED.sales_growth,
                    pledged_perc = EXCLUDED.pledged_perc,
                    cash_equiv = EXCLUDED.cash_equiv,
                    debt_equiv = EXCLUDED.debt_equiv,
                    interest_cov = EXCLUDED.interest_cov,
                    reserves = EXCLUDED.reserves,
                    face_value = EXCLUDED.face_value,
                    last_updated = NOW();
            """, (
                data.get('symbol'), data.get('company_name'), data.get('Current Price'), data.get('PE Ratio'),
                data.get('Market Cap'), data.get('ROCE'), data.get('ROE'), data.get('Dividend Yield'),
                data.get('Sales Growth'), data.get('Pledged %'), data.get('Cash Equivalent'),
                data.get('Debt Equivalent'), data.get('Interest Cover'), data.get('Reserves'),
                data.get('Face Value')
            ))
            conn.commit()
            cur.close()
            logging.info(f"Data for {data.get('symbol')} saved to database.")
        except Exception as e:
            logging.error(f"Error saving data to database: {e}")
        finally:
            conn.close()

def load_stock_data(symbol, max_age_hours=24):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM stock_data WHERE symbol = %s;", (symbol,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                # Convert row to dictionary for easier access
                # (You might need to adjust column order based on your actual table)
                cols = ['symbol', 'company_name', 'cmp', 'pe_ratio', 'market_cap', 'roce', 'roe', 'div_yield',
                        'sales_growth', 'pledged_perc', 'cash_equiv', 'debt_equiv', 'interest_cov',
                        'reserves', 'face_value', 'last_updated']
                data = dict(zip(cols, row))

                # Check if data is fresh enough
                if (datetime.now() - data['last_updated']) < timedelta(hours=max_age_hours):
                    logging.info(f"Serving fresh data for {symbol} from database.")
                    return data
                else:
                    logging.info(f"Data for {symbol} is stale, needs re-scraping.")
                    return None # Data is stale, force re-scrape
            return None # Not found in DB
        except Exception as e:
            logging.error(f"Error loading data from database: {e}")
            return None
    return None # No DB connection


# --- Selenium Scraping Function ---
def get_stock_data_from_screener(stock_symbol):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36")
    # Add an argument for specific binary path if using custom Chrome build (less common on Render)
    # options.binary_location = "/usr/bin/google-chrome" # For example, if you explicitly install Chrome

    driver = None # Initialize driver to None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logging.info(f"Selenium WebDriver initialized for {stock_symbol}.")

        url = f"https://www.screener.in/company/{stock_symbol}/"
        driver.get(url)

        # Wait for a key element to be present to ensure page is loaded
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//h1[@class='margin-0 margin-bottom-1']"))
        )
        logging.info(f"Page loaded for {stock_symbol}.")

        scraped_data = {"symbol": stock_symbol}

        # --- Scraping Logic (using your XPaths) ---
        # It's crucial to wrap each find_element in a try-except to prevent crashes
        # if an element is not found on the page.

        try:
            scraped_data['company_name'] = driver.find_element(By.XPATH, "//h1[@class='margin-0 margin-bottom-1']").text
        except Exception:
            scraped_data['company_name'] = 'N/A'

        try:
            scraped_data['Current Price'] = driver.find_element(By.XPATH, "//span[@class='font-weight-semibold d-block']").text
        except Exception:
            scraped_data['Current Price'] = 'N/A'

        # Example for one ratio, repeat for all others you need
        # Scrape all ratio values
        ratio_labels = driver.find_elements(By.XPATH, "//span[@class='name']")
        ratio_values = driver.find_elements(By.XPATH, "//span[@class='value']")

        for i in range(len(ratio_labels)):
            try:
                label = ratio_labels[i].text.strip()
                value = ratio_values[i].text.strip()
                scraped_data[label] = value
            except IndexError:
                logging.warning(f"Mismatch in ratio labels/values at index {i}")
            except Exception as e:
                logging.error(f"Error scraping ratio: {e}")

        # You might have specific XPaths for balance sheet data etc.
        # e.g., for Cash Equivalents:
        # try:
        #     scraped_data['Cash Equivalent'] = driver.find_element(By.XPATH, "your_xpath_for_cash_equivalent").text
        # except Exception:
        #     scraped_data['Cash Equivalent'] = 'N/A'
        # Do this for all other specific data points you need.

        logging.info(f"Scraping completed for {stock_symbol}.")
        return scraped_data

    except Exception as e:
        logging.error(f"Error during Selenium scraping for {stock_symbol}: {e}")
        return None
    finally:
        if driver:
            driver.quit()
            logging.info(f"Selenium WebDriver for {stock_symbol} quit.")

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_stock_data', methods=['POST'])
def handle_stock_request():
    symbol = request.form['symbol'].upper() # Get symbol from form, convert to uppercase
    logging.info(f"Received request for stock symbol: {symbol}")

    # Try to load data from DB first
    stock_data = load_stock_data(symbol)

    if stock_data:
        logging.info(f"Found fresh data for {symbol} in DB.")
        # Remove 'last_updated' as it's internal
        stock_data.pop('last_updated', None)
        return jsonify(stock_data)
    else:
        logging.info(f"Data for {symbol} not in DB or stale, initiating scrape.")
        scraped_data = get_stock_data_from_screener(symbol)
        if scraped_data:
            save_stock_data(scraped_data) # Save newly scraped data to DB
            # Remove 'symbol' as it's the key, not a displayed value
            scraped_data.pop('symbol', None)
            return jsonify(scraped_data)
        else:
            return jsonify({"error": "Failed to retrieve stock data."}), 500

# Entry point for Gunicorn
# This block is REMOVED because Gunicorn handles app startup
# if __name__ == '__main__':
#     # Initialize database on app startup if you want
#     # In production, you might run this as a separate one-off command
#     # or ensure your Render build step sets up the DB
#     setup_database()
#     app.run(debug=True)
