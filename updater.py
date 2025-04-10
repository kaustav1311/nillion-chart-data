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
        "days": 2  # Pulls yesterday + today (implicitly hourly granularity)
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NillionBot/1.0)"
    }
    res = requests.get(url, params=params, headers=headers)
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

def get_ohlc(chart_data, target_date, next_date):
    prices = chart_data.get("prices", [])
    
    day_prices = [(ts, price) for ts, price in prices
                  if datetime.utcfromtimestamp(ts / 1000).date() == target_date]

    next_day_prices = [(ts, price) for ts, price in prices
                       if datetime.utcfromtimestamp(ts / 1000).date() == next_date]

    if not day_prices:
        raise ValueError("No price data for target day")

    open_price = round(day_prices[0][1], 6)
    close_price = round(next_day_prices[0][1], 6) if next_day_prices else None
    high = round(max(price for _, price in day_prices), 6)
    low = round(min(price for _, price in day_prices), 6)

    return open_price, high, low, close_price

def update_daily_json(new_entry):
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError("chart_data/daily.json not found")

    with open(DATA_PATH, "r") as f:
        data = json.load(f)

    if any(entry["date"] == new_entry["date"] for entry in data):
        print("ℹ️ Entry for this date already exists. Skipping.")
        return

    data.append(new_entry)
    #data = data[-30:]

    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Added: {new_entry['date']}")

def main():
    print("🚀 Running daily updater...")

    chart_data = fetch_market_chart()
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    today = yesterday + timedelta(days=1)

    date_str = yesterday.strftime("%b %d")
    print(f"📅 Processing for: {date_str}")

    time.sleep(3)
    volume = fetch_yesterdays_volume(yesterday)
    open_p, high, low, close_p = get_ohlc(chart_data, yesterday, today)

    if close_p is None:
        raise ValueError("Close price (from today 00:00 UTC) not yet available.")

    new_entry = {
        "date": date_str,
        "open": open_p,
        "high": high,
        "low": low,
        "close": close_p,
        "volume": volume
    }

    update_daily_json(new_entry)

if __name__ == "__main__":
    main()
