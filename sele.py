from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import shutil, os

def run_scraper(query):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = "/usr/bin/google-chrome"

    service = Service("/usr/local/bin/chromedriver")

    # Diagnostics
    print("PATH:", os.environ.get("PATH"))
    print("google-chrome:", shutil.which("google-chrome"))
    print("chromedriver:", shutil.which("chromedriver"))

    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(f"https://example.com/?q={query}")
        return driver.title
    except Exception as e:
        return f"❌ Error: {e}"
    finally:
        driver.quit()
