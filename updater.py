import requests
import json
from datetime import datetime, timedelta, UTC
import os

COIN_ID = "nillion"
VS_CURRENCY = "usd"
DAILY_FILE = "chart_data/daily.json"

def get_date_labels():
    today = datetime.now(UTC).date()
    yesterday = today - timedelta(days=1)
    date_str = yesterday.strftime("%b %d")       # For JSON label
    date_query = yesterday.strftime("%d-%m-%Y")   # For CoinGecko /history
    return yesterday, date_str, date_query

def fetch_hourly_prices():
    url = f"https://api.coingecko.com/api/v3/coins/{COIN_ID}/market_chart"
    params = {
        "vs_currency": VS_CURRENCY,
        "days": 2,
        "interval": "hourly"
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()["prices"]

def filter_prices_by_day(prices, day):
    return [price for ts, price in prices if datetime.utcfromtimestamp(ts / 1000).date() == day]

def get_open_close(prices, yesterday, today):
    open_price = prices[0][1]  # First hourly price of yesterday
    close_price = None

    for ts, price in prices:
        timestamp = datetime.utcfromtimestamp(ts / 1000).date()
        if timestamp == today:
            close_price = price
            break

    if close_price is None:
        raise ValueError("Close price (from today 00:00 UTC) not found.")

    return round(open_price, 6), round(close_price, 6)

def get_volume(date_query):
    url = f"https://api.coingecko.com/api/v3/coins/{COIN_ID}/history"
    params = {"date": date_query}
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()
    volume = data.get("market_data", {}).get("total_volume", {}).get("usd")
    return round(volume / 1_000_000, 2) if volume else 0

def update_json(data_obj):
    if not os.path.exists(DAILY_FILE):
        existing = []
    else:
        with open(DAILY_FILE, "r") as f:
            existing = json.load(f)

    existing.append(data_obj)
    latest_30 = existing[-30:]

    with open(DAILY_FILE, "w") as f:
        json.dump(latest_30, f, indent=2)
    print(f"✅ Appended {data_obj['date']} to daily.json")

def main():
    print("🚀 Running updater.py...")
    yesterday, date_str, date_query = get_date_labels()
    today = yesterday + timedelta(days=1)

    print(f"📅 Targeting full day: {date_str}")

    prices_raw = fetch_hourly_prices()
    prices_yday = filter_prices_by_day(prices_raw, yesterday)

    if not prices_yday:
        raise ValueError("No hourly prices found for yesterday.")

    high = round(max(price for _, price in prices_yday), 6)
    low = round(min(price for _, price in prices_yday), 6)
    open_price, close_price = get_open_close(prices_yday + prices_raw, yesterday, today)
    volume = get_volume(date_query)

    entry = {
        "date": date_str,
        "open": open_price,
        "high": high,
        "low": low,
        "close": close_price,
        "volume": volume
    }

    update_json(entry)

if __name__ == "__main__":
    main()
