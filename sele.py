# sele.py
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
import time 
import re
import sys
import string
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

sys.stdout.reconfigure(encoding='utf-8') # Good for console output

def get_element_text(driver, by_method, locator, timeout=10, default_value="N/A", log_error=True):
    """
    Safely finds an element and extracts its text using explicit waits.
    Returns default_value if element is not found within timeout.
    """
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by_method, locator))
        )
        return element.text.strip()
    except Exception as e:
        if log_error:
            logging.warning(f"Could not find element with {by_method}='{locator}' within {timeout}s. Error: {e}. Setting to '{default_value}'.")
        return default_value

def get_elements(driver, by_method, locator, timeout=10, log_error=True):
    """
    Safely finds multiple elements using explicit waits.
    Returns an empty list if elements are not found within timeout.
    """
    try:
        elements = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((by_method, locator))
        )
        return elements
    except Exception as e:
        if log_error:
            logging.warning(f"Could not find any elements with {by_method}='{locator}' within {timeout}s. Error: {e}. Returning empty list.")
        return []

def extract_number(text):
    # This function is good, keep it as is
    matches = re.findall(r'[\d,.]+', text)
    if matches:
        num = matches[0].replace(',', '')
        try:
            return float(num)
        except ValueError:
            pass
    return 0.0

def annual_info(driver):
    annual_data = {}
    
    # --- Annual Sales ---
    # Wait for the first row of sales data to be present
    sales_cells = get_elements(driver, By.XPATH, '//*[@id="profit-loss"]/div[3]/table/tbody/tr[1]/td')
    sales = []
    if not sales_cells:
        logging.error("Could not find annual sales row. Skipping annual info.")
        return {} # Return empty if core elements not found

    # Assuming the first cell is a label, start from the second for data
    num_cols = len(sales_cells)
    nca = num_cols # Store num_cols for consistency checks

    for i in range(2, num_cols + 1):
        svalue = get_element_text(driver, By.XPATH, f'//*[@id="profit-loss"]/div[3]/table/tbody/tr[1]/td[{i}]')
        salesnum = extract_number(svalue)
        sales.append(salesnum)
    annual_data["asales"] = sales

    # --- Annual Other Income ---
    oincome = []
    for i in range(2, num_cols + 1): # Use nca (num_cols from sales) for consistency
        oivalue = get_element_text(driver, By.XPATH, f'//*[@id="profit-loss"]/div[3]/table/tbody/tr[5]/td[{i}]')
        oinum = extract_number(oivalue)
        oincome.append(oinum)
    annual_data["aOther_Income"] = oincome

    # --- Total Revenue ---
    totrev = []
    for i in range(0, len(sales) -1): # Adjust range based on actual sales length
        val = oincome[i] + sales[i]
        totrev.append(val)
    annual_data["aTotal_Revenue"] = totrev

    # --- Revenue Growth ---
    rg = ['0%'] # Initialize with string '0%'
    for i in range(0, len(totrev) - 1): # Corrected loop for growth calculation
        if totrev[i] != 0: # Avoid division by zero
            val = (totrev[i+1] - totrev[i]) * 100 / totrev[i]
            rounded = round(val, 2)
            rg.append(f"{rounded}%")
        else:
            rg.append("N/A")
    annual_data["aRevenue_Growth"] = rg

    # --- Consolidated Net Profit ---
    np_cells = get_elements(driver, By.XPATH, '//*[@id="profit-loss"]/div[3]/table/tbody/tr[10]/td')
    np = []
    for i in range(1, len(np_cells) + 1): # Loop through found cells
        npnum = get_element_text(driver, By.XPATH, f'//*[@id="profit-loss"]/div[3]/table/tbody/tr[10]/td[{i}]')
        npp = extract_number(npnum)
        np.append(npp)
    annual_data["aNet_Profit"] = np

    # --- Net Profit Margin ---
    npm = []
    for i in range(0, len(np) - 1): # Use actual length of np
        if totrev[i] != 0: # Avoid division by zero
            val = (np[i] / totrev[i]) * 100
            rounded = round(val, 2)
            npm.append(f"{rounded}%")
        else:
            npm.append("N/A")
    annual_data["aNet_Profit_Margin"] = npm

    # --- EPS ---
    eps_cells = get_elements(driver, By.XPATH, '//*[@id="profit-loss"]/div[3]/table/tbody/tr[11]/td')
    eps = []
    for i in range(2, len(eps_cells) + 1): # Start from 2 if first is label
        epsnum = get_element_text(driver, By.XPATH, f'//*[@id="profit-loss"]/div[3]/table/tbody/tr[11]/td[{i}]')
        epsn = extract_number(epsnum)
        eps.append(epsn)
    annual_data["aEPS"] = eps

    # --- EPS Growth ---
    epsg = ['0%'] # Initialize with string '0%'
    for i in range(0, len(eps) - 1): # Corrected loop for growth calculation
        if eps[i] != 0: # Avoid division by zero
            val = (eps[i+1] - eps[i]) * 100 / eps[i]
            rounded = round(val, 2)
            epsg.append(f"{rounded}%")
        else:
            epsg.append("N/A")
    annual_data["aEPS_Growth"] = epsg

    # --- Dividend Payout ---
    dp_cells = get_elements(driver, By.XPATH, '//*[@id="profit-loss"]/div[3]/table/tbody/tr[12]/td')
    dp = []
    for i in range(1, len(dp_cells) + 1):
        dpnum = get_element_text(driver, By.XPATH, f'//*[@id="profit-loss"]/div[3]/table/tbody/tr[12]/td[{i}]')
        # Here you extract number_string, but append dpnum (the original text).
        # Adjust based on what you want to store (raw text or extracted number)
        number_string = re.findall(r'[\d,\.]+', dpnum)
        if number_string: # Only append if a number-like string is found
            dp.append(dpnum)
        else:
            dp.append("N/A")
    annual_data["aDivident_Payout"] = dp

    # --- Promoter, FII, DII Annual (Shareholding) ---
    # Click annual button and wait for table to be present
    try:
        driver.find_element(By.XPATH,'//*[@id="shareholding"]/div[1]/div[2]/div[1]/button[2]').click()
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="yearly-shp"]/div/table'))
        )
        logging.info("Clicked Annual shareholding and table loaded.")
    except Exception as e:
        logging.warning(f"Could not click Annual shareholding button or table not found: {e}")
        # If this fails, the rest of annual shareholding will fail, so return what we have
        return annual_data

    # This part can be generalized for all shareholding types (Promoter, FII, DII)
    shareholding_types = {
        "aPromoter": 1,
        "aFII": 2,
        "aDII": 3
    }
    
    for key, row_idx in shareholding_types.items():
        current_list = []
        shp_cells = get_elements(driver, By.XPATH, f'//*[@id="yearly-shp"]/div/table/tbody/tr[{row_idx}]/td')
        
        # Ensure 'nca' (number of columns from profit-loss) is defined if needed for NA padding
        # If shp_cells are fewer than nca, prepend 'NA'
        if nca and len(shp_cells) < nca:
            for _ in range(nca - len(shp_cells)):
                current_list.append("NA")

        for cell_idx in range(1, len(shp_cells) + 1):
            sh_val = get_element_text(driver, By.XPATH, f'//*[@id="yearly-shp"]/div/table/tbody/tr[{row_idx}]/td[{cell_idx}]')
            number_string = re.findall(r'[\d\.]+', sh_val)
            if not number_string:
                current_list.append("N/A") # Changed from 'continue' to append 'N/A'
            else:
                current_list.append(sh_val)
        annual_data[key] = current_list
    
    return annual_data

def quaterly_info(driver):
    quaterly_data = {}

    # --- Quarterly Sales ---
    qsales_cells = get_elements(driver, By.XPATH, '//*[@id="quarters"]/div[3]/table/tbody/tr[1]/td')
    qsales = []
    if not qsales_cells:
        logging.error("Could not find quarterly sales row. Skipping quarterly info.")
        return {}

    num_cols = len(qsales_cells)
    nc = num_cols

    for i in range(2, num_cols + 1):
        qsvalue = get_element_text(driver, By.XPATH, f'//*[@id="quarters"]/div[3]/table/tbody/tr[1]/td[{i}]')
        qsalesnum = extract_number(qsvalue)
        qsales.append(qsalesnum)
    quaterly_data["qsales"] = qsales

    # --- Quarterly Other Income ---
    qoincome = []
    for i in range(2, num_cols + 1):
        qoivalue = get_element_text(driver, By.XPATH, f'//*[@id="quarters"]/div[3]/table/tbody/tr[5]/td[{i}]')
        qoinum = extract_number(qoivalue)
        qoincome.append(qoinum)
    quaterly_data["qOther_Income"] = qoincome

    # --- Total Revenue Quarterly ---
    qtotrev = []
    for i in range(0, len(qsales) - 1): # Adjusted range
        val = qoincome[i] + qsales[i]
        qtotrev.append(val)
    quaterly_data["qTotal_Revenue"] = qtotrev

    # --- Revenue Growth Quarterly ---
    rgq = ['0%']
    for i in range(0, len(qtotrev) - 1):
        if qtotrev[i] != 0:
            val = (qtotrev[i+1] - qtotrev[i]) * 100 / qtotrev[i]
            rounded = round(val, 2)
            rgq.append(f"{rounded}%")
        else:
            rgq.append("N/A")
    quaterly_data["qRevenue_Growth"] = rgq

    # --- Consolidated Net Profit Quarterly ---
    # NOTE: The XPath for npq_row was //*[@id="quarters"]/div[3]/table/tbody/tr[1]/td in your original, which seems wrong (it's the sales row).
    # Assuming it should be tr[10] like annual info. Please verify this XPath.
    npq_cells = get_elements(driver, By.XPATH, '//*[@id="quarters"]/div[3]/table/tbody/tr[10]/td')
    npq = []
    for i in range(1, len(npq_cells) + 1):
        npqnum = get_element_text(driver, By.XPATH, f'//*[@id="quarters"]/div[3]/table/tbody/tr[10]/td[{i}]')
        nppq = extract_number(npqnum)
        npq.append(nppq)
    quaterly_data["qNet_Profit"] = npq

    # --- Net Profit Margin Quarterly ---
    npqm = []
    for i in range(0, len(npq) - 1):
        if qtotrev[i] != 0:
            val = (npq[i] / qtotrev[i]) * 100
            rounded = round(val, 2)
            npqm.append(f"{rounded}%")
        else:
            npqm.append("N/A")
    quaterly_data["qNet_Profit_Margin"] = npqm

    # --- EPS Quarterly ---
    epsq_cells = get_elements(driver, By.XPATH, '//*[@id="quarters"]/div[3]/table/tbody/tr[11]/td')
    epsq = []
    for i in range(2, len(epsq_cells) + 1):
        epsqnum = get_element_text(driver, By.XPATH, f'//*[@id="quarters"]/div[3]/table/tbody/tr[11]/td[{i}]')
        epsqn = extract_number(epsqnum)
        epsq.append(epsqn)
    quaterly_data["qEPS"] = epsq

    # --- EPS Growth Quarterly ---
    epsgq = ['0%']
    for i in range(0, len(epsq) - 1):
        if epsq[i] != 0:
            val = (epsq[i+1] - epsq[i]) * 100 / epsq[i]
            rounded = round(val, 2)
            epsgq.append(f"{rounded}%")
        else:
            epsgq.append("N/A")
    quaterly_data["qEPS_Growth"] = epsgq

    # --- Promoter, FII, DII Quarterly (Shareholding) ---
    # These XPaths were all pointing to tr[1]/td for num_cols calculation.
    # Corrected to use common pattern, ensure correct row for each.
    shareholding_types = {
        "qPromoter": 1,
        "qFII": 2,
        "qDII": 3 # Assuming DII is row 3 like annual
    }
    
    for key, row_idx in shareholding_types.items():
        current_list = []
        shp_cells = get_elements(driver, By.XPATH, f'//*[@id="quarterly-shp"]/div/table/tbody/tr[{row_idx}]/td')
        
        if nc and len(shp_cells) < nc: # Use 'nc' from quarterly sales
            for _ in range(nc - len(shp_cells)):
                current_list.append("NA")

        for cell_idx in range(1, len(shp_cells) + 1):
            sh_val = get_element_text(driver, By.XPATH, f'//*[@id="quarterly-shp"]/div/table/tbody/tr[{row_idx}]/td[{cell_idx}]')
            number_string = re.findall(r'[\d\.]+', sh_val)
            if not number_string:
                current_list.append("N/A")
            else:
                current_list.append(sh_val)
        quaterly_data[key] = current_list

    return quaterly_data

def run_scraper(stock):
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36")
    # Add a window size to prevent elements from being hidden on a small default headless window
    options.add_argument("--window-size=1920,1080")
    
    driver = None # Initialize to None for finally block
    try:
        driver = uc.Chrome(options=options)
        logging.info(f"Selenium WebDriver initialized for {stock} using undetected_chromedriver.")

        # Navigate to screener.in and wait for search input
        driver.get("https://www.screener.in/")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/main/div[2]/div/div/div/input"))
        )
        logging.info("Screener.in loaded. Entering stock symbol.")

        # ENTER user-specified stock
        search_input = driver.find_element(By.XPATH, "/html/body/main/div[2]/div/div/div/input")
        search_input.send_keys(stock)
        
        # Wait for search suggestion to appear and click the first one
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/main/div[2]/div/div/div/ul/li[1]"))
        ).click()
        logging.info(f"Clicked on first search suggestion for {stock}.")

        # Wait for the company page to load, e.g., company name H1
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//h1[@class='margin-0 margin-bottom-1']"))
        )
        logging.info(f"Company page loaded for {stock}.")

        # --- Scraping main ratios and shareholding patterns ---
        # Replaced direct find_element with get_element_text helper
        PROMOTERS = get_element_text(driver, By.XPATH, '//*[@id="quarterly-shp"]/div/table/tbody/tr[1]/td[13]')
        FII = get_element_text(driver, By.XPATH, '//*[@id="quarterly-shp"]/div/table/tbody/tr[2]/td[13]')
        DII = get_element_text(driver, By.XPATH, '//*[@id="quarterly-shp"]/div/table/tbody/tr[3]/td[13]')
        PUBLIC = get_element_text(driver, By.XPATH, '//*[@id="quarterly-shp"]/div/table/tbody/tr[5]/td[13]')
        CMP = get_element_text(driver, By.XPATH, '//*[@id="top-ratios"]/li[2]/span[2]/span')
        F_HIGH = get_element_text(driver, By.XPATH, '//*[@id="top-ratios"]/li[3]/span[2]/span[1]')
        F_LOW = get_element_text(driver, By.XPATH, '//*[@id="top-ratios"]/li[3]/span[2]/span[2]')
        
        cmpn=extract_number(CMP)
        fln=extract_number(F_LOW)
        fhn=extract_number(F_HIGH)
        HLP = 0.0
        if fhn - fln != 0: # Avoid division by zero
            HLP = ((cmpn - fln) * 100) / (fhn - fln)
        roundedh = round(HLP, 2)
        hlper=f"{roundedh}%"
        
        PB = get_element_text(driver, By.XPATH, '//*[@id="top-ratios"]/li[5]/span[2]')

        # Click for PE 5yr chart data and wait for it to update
        try:
            driver.find_element(By.XPATH, '//*[@id="company-chart-metrics"]/button[2]').click() # PE button
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="chart-legend"]/label[2]/span')) # Wait for PE legend
            )
            logging.info("Clicked PE chart metric.")
        except Exception as e:
            logging.warning(f"Could not click PE chart metric button: {e}")

        pe_5yr_f = get_element_text(driver, By.XPATH, '//*[@id="chart-legend"]/label[2]/span')
        pe5l = pe_5yr_f.split()
        pe_5yr = pe5l[3] if len(pe5l) > 3 else "N/A"

        # Click for PE 3yr chart data
        try:
            driver.find_element(By.XPATH, '//*[@id="company-chart-days"]/button[4]').click()
            WebDriverWait(driver, 5).until( # Wait for the element that updates for 3yr
                EC.presence_of_element_located((By.XPATH, '/html/body/main/section[1]/div[3]/label[2]/span')) # Check if this XPath truly updates or if it's the same
            )
            logging.info("Clicked 3yr chart period.")
        except Exception as e:
            logging.warning(f"Could not click 3yr chart period button: {e}")

        pe_3yr_f = get_element_text(driver, By.XPATH, '/html/body/main/section[1]/div[3]/label[2]/span')
        pe3l = pe_3yr_f.split()
        pe_3yr = pe3l[3] if len(pe3l) > 3 else "N/A"

        # Click for PE 1yr chart data
        try:
            driver.find_element(By.XPATH, '//*[@id="company-chart-days"]/button[3]').click()
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="chart-legend"]/label[2]/span'))
            )
            logging.info("Clicked 1yr chart period.")
        except Exception as e:
            logging.warning(f"Could not click 1yr chart period button: {e}")

        pe_1yr_f = get_element_text(driver, By.XPATH, '//*[@id="chart-legend"]/label[2]/span')
        pe1l = pe_1yr_f.split()
        pe_1yr = pe1l[3] if len(pe1l) > 3 else "N/A"

        # Click for PE 10yr chart data
        try:
            driver.find_element(By.XPATH, '//*[@id="company-chart-days"]/button[6]').click()
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="chart-legend"]/label[2]/span'))
            )
            logging.info("Clicked 10yr chart period.")
        except Exception as e:
            logging.warning(f"Could not click 10yr chart period button: {e}")

        pe_10yr_f = get_element_text(driver, By.XPATH, '//*[@id="chart-legend"]/label[2]/span')
        pe10l = pe_10yr_f.split()
        pe_10yr = pe10l[3] if len(pe10l) > 3 else "N/A"

        DY = get_element_text(driver, By.XPATH, '//*[@id="top-ratios"]/li[6]/span[2]/span')
        
        # Run the two functions
        # Ensure these functions also use the get_element_text helper
        quaterly_data = quaterly_info(driver)
        annual_data = annual_info(driver)

        # RETURN collected data as a dict:
        return {
            "PROMOTERS": PROMOTERS,
            "FII": FII,
            "DII": DII,
            "PUBLIC": PUBLIC,
            "CMP": CMP,
            "F_HIGH": F_HIGH,
            "F_LOW": F_LOW,
            "HiLoPer": hlper,
            "PB": PB,
            "pe_1yr": pe_1yr,
            "pe_3yr": pe_3yr,
            "pe_5yr": pe_5yr,
            "pe_10yr": pe_10yr,
            "DY": DY,
            **quaterly_data,
            **annual_data
        }

    except Exception as e:
        logging.error(f"An unexpected error occurred in run_scraper for {stock}: {e}")
        return None
    finally:
        if driver:
            driver.quit()
            logging.info("Selenium WebDriver quit.")

# Allow standalone use:
if __name__ == "__main__":
    stock_symbol = input("Enter stock name or symbol: ")
    result = run_scraper(stock_symbol)
    if result:
        # If running standalone, print the result in a readable format
        for key, value in result.items():
            print(f"{key}: {value}")
    else:
        print("Scraping failed or returned no data.")
