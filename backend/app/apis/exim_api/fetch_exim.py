import requests
from bs4 import BeautifulSoup

def fetch_trade_data_for_year(year: str, hs_code: str, report_type: int = 2, commodity_type: str = "specific"):
    base_url = "https://tradestat.commerce.gov.in"
    endpoint = "/eidb/commodity_wise_export"

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Referer": base_url,
        "Origin": base_url
    })

    # 1. Get CSRF token
    r = session.get(base_url + endpoint, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    token_input = soup.find("input", {"name": "_token"})
    if not token_input:
        raise RuntimeError("CSRF token not found")

    csrf_token = token_input["value"]

    # 2. POST request
    payload = {
        "_token": csrf_token,
        "EidbYearCwe": year,
        "commodityType": commodity_type,
        "Eidb_hscodeCwe": hs_code,
        "Eidb_ReportCwe": report_type
    }

    response = session.post(base_url + endpoint, data=payload, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", {"id": "example1"})
    if not table:
        raise RuntimeError(f"Trade table not found for {year}")

    headers = [th.get_text(strip=True) for th in table.thead.find_all("th")]

    rows = []
    for tr in table.tbody.find_all("tr"):
        cols = [td.get_text(strip=True).replace(",", "") for td in tr.find_all("td")]
        rows.append(dict(zip(headers, cols)))

    totals = {}
    if table.tfoot:
        footer_cols = [td.get_text(strip=True).replace(",", "") for td in table.tfoot.find_all("td")]
        totals = dict(zip(headers, footer_cols))

    return {
        "year": year,
        "columns": headers,
        "rows": rows,
        "totals": totals
    }


def fetch_trade_data(hs_code: str):
    all_data = {}

    for year in range(2019, 2026):  # 2019 to 2025 inclusive
        print(f"Fetching data for {year}...")
        try:
            all_data[str(year)] = fetch_trade_data_for_year(str(year), hs_code)
        except Exception as e:
            print(f"Failed for {year}: {e}")
            all_data[str(year)] = None

    return {
        "hs_code": hs_code,
        "data_by_year": all_data
    }


if __name__ == "__main__":
    data = fetch_trade_data("30049099")
    print(data)
