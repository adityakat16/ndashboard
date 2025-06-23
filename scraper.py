import requests
from bs4 import BeautifulSoup

def get_stock_data(stock_code):
    url = f"https://www.screener.in/company/{stock_code}/"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers, timeout=5)
    if r.status_code != 200:
        return f"❌ Failed to fetch. Status: {r.status_code}"

    soup = BeautifulSoup(r.text, "html.parser")
    title_h1 = soup.find("h1")
    if not title_h1:
        return "❌ Invalid stock code or layout changed"

    name = title_h1.text.strip()
    price_el = soup.select_one(".price-panel .number")
    price = price_el.text.strip() if price_el else "N/A"

    ratios = []
    for row in soup.select("#top-ratios .row"):
        cells = row.get_text(strip=True, separator=" | ")
        ratios.append(cells)
    ratios_text = "\n".join(ratios)

    return f"✅ {name}\n💰 Price: {price}\n\n📊 Top Ratios:\n{ratios_text}"
