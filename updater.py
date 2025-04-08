import requests
import json
from datetime import datetime, timedelta
import time
import os

DATA_PATH = "chart_data/daily.json"
COIN_ID = "nillion"

def fetch_market_chart():
    url = f"https://api.coingecko.com/api/v3/coins/{COIN_ID}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": 2  # Get today + yesterday
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()

def fetch_yesterdays_volume(date_obj):
    date_str = date_obj.strftime("%d-%m-%Y")
    url = f"https://api.coingecko.com/api/v3/coins/{COIN_ID}/history"
    params = {"date": date_str}
    res = requests.get(url, params=params)
    if res.status_code != 200:
        raise ValueError(f"HTTP {res.status_code} on /history")

    data = res.json()
    volume = data.get("market_data", {}).get("total_volume", {}).get("usd")
    if volume is None:
        raise ValueError("Missing volume data")
    return round(volume / 1_000_000, 2)

def get_yesterday_high_low(chart_data, date_obj):
    prices = chart_data.get("prices", [])
    target_date = date_obj.date()

    daily_prices = [price for ts, price in prices
                    if datetime.utcfromtimestamp(ts / 1000).date() == target_date]

    if not daily_prices:
        raise ValueError("No price data for yesterday")

    high = round(max(daily_prices), 6)
    low = round(min(daily_prices), 6)
    return high, low

def update_daily_json(new_entry):
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError("chart_data/daily.json not found")

    with open(DATA_PATH, "r") as f:
        data = json.load(f)

    # Don't duplicate if already present
    if any(entry["date"] == new_entry["date"] for entry in data):
        print("ℹ️ Entry for this date already exists. Skipping.")
        return

    data.append(new_entry)
    data = data[-29:]

    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Added: {new_entry['date']}")

def main():
    print("🚀 Running daily updater...")
    chart_data = fetch_market_chart()

    yesterday = datetime.utcnow() - timedelta(days=1)
    date_str = yesterday.strftime("%b %d")

    print(f"📅 Processing for: {date_str}")

    time.sleep(3)
    volume = fetch_yesterdays_volume(yesterday)
    high, low = get_yesterday_high_low(chart_data, yesterday)

    new_entry = {
        "date": date_str,
        "high": high,
        "low": low,
        "volume": volume
    }

    update_daily_json(new_entry)

if __name__ == "__main__":
    main()
