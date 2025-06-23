from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc

def run_scraper(stock):
    try:
        options = uc.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = uc.Chrome(options=options)
        driver.get(f"https://www.google.com/search?q={stock}+stock")
        result = driver.title
        driver.quit()
        return result
    except Exception as e:
        return f"❌ Error during scraping: {e}"
