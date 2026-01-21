import os
import sys
import json
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

# Add path for clients
sys.path.append(os.path.join(os.path.dirname(__file__), 'kalshi-starter-code-python'))
from clients import KalshiHttpClient, Environment

def get_initialized_client():
    """Handles setup logic and returns a ready-to-use KalshiHttpClient."""
    load_dotenv()
    env = Environment.PROD 
    KEYID = os.getenv('PROD_KEYID')
    KEYFILE = os.getenv('PROD_KEYFILE')
    if not KEYFILE:
        raise ValueError("PROD_KEYFILE path not found in .env")
    with open(KEYFILE, "rb") as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None)
    return KalshiHttpClient(key_id=KEYID, private_key=private_key, environment=env)

def find_game_in_series(client, series_ticker, search_terms):
    """Finds games within a series where ALL search terms appear in the TICKER."""
    my_cursor = None
    matching_tickers = []
    while True:
        response = client.get_markets(series_ticker=series_ticker, limit=100, cursor=my_cursor)
        markets = response.get('markets', [])
        for m in markets:
            ticker = m.get('ticker', '').upper()
            if all(term.upper() in ticker for term in search_terms):
                matching_tickers.append(ticker)
        my_cursor = response.get('cursor')
        if not my_cursor or not markets:
            break
    return matching_tickers

def get_market_odds(client, ticker):
    """Fetches market details and prints the Yes Ask (Market Price) and Volume."""
    try:
        data = client.get_market(ticker)
        market = data.get('market', {})
        title = market.get('title', 'Unknown')
        price = market.get('yes_ask')
        volume = market.get('volume', 0)
        print(f"--- {title} ---")
        print(f"Ticker:       {ticker}")
        print(f"Market Price: {price} cents")
        print(f"Total Volume: {volume}\n")
    except Exception as e:
        print(f"Error fetching odds for {ticker}: {e}")

def get_binary_outcomes(client, series_ticker, team1, team2):
    """Consolidated function to find a matchup and print odds."""
    search_terms = [team1, team2]
    print(f"\n>>> Searching {series_ticker} for: {team1} vs {team2}...")
    tickers = find_game_in_series(client, series_ticker, search_terms)
    if tickers:
        print(f"Found {len(tickers)} related markets. Fetching odds...\n")
        for t in tickers:
            get_market_odds(client, t)
    else:
        print("No markets found matching both teams.")

def get_series_outcomes(client, series_ticker, filter_extremes=True):
    """
    Fetches ALL markets in a series (e.g. Championship Futures),
    and prints them sorted by their 'Yes' price (probability).
    
    Args:
        filter_extremes (bool): If True, hides markets with price <= 1 or >= 99.
    """
    print(f"\n>>> Fetching all outcomes for series: {series_ticker}...")
    
    all_markets = []
    my_cursor = None
    
    # 1. Fetch all markets in the series
    while True:
        response = client.get_markets(series_ticker=series_ticker, limit=100, cursor=my_cursor)
        markets = response.get('markets', [])
        all_markets.extend(markets)
        
        my_cursor = response.get('cursor')
        if not my_cursor or not markets:
            break
            
    # 2. Sort by price (yes_ask) descending. 
    all_markets.sort(key=lambda x: x.get('yes_ask') or 0, reverse=True)
    
    print(f"Found {len(all_markets)} total outcomes.")
    if filter_extremes:
        print("Filtering out prices <= 1¢ and >= 99¢...\n")
    else:
        print("Showing all prices...\n")
    
    for m in all_markets:
        ticker = m.get('ticker')
        title = m.get('title')
        subtitle = m.get('subtitle', '')
        price = m.get('yes_ask')
        volume = m.get('volume')
        
        # Handle None price
        if price is None: price = 0
        
        # Apply filter
        if filter_extremes and (price <= 1 or price >= 99):
            continue
            
        print(f"{price}¢  - [{ticker}] {title} {subtitle} (Vol: {volume})")

def get_market_probability(client, ticker):
    """
    Outputs the BUY YES and BUY NO prices for a specific market ticker.
    These values represent the market's implied probability for each outcome.
    """
    try:
        data = client.get_market(ticker)
        market = data.get('market', {})
        title = market.get('title', 'Unknown')
        yes_price = market.get('yes_ask')
        no_price = market.get('no_ask')
        print(f"\n>>> Probabilities for: {title}")
        print(f"Ticker:  {ticker}")
        print(f"YES:     {yes_price}% ({yes_price}¢)")
        print(f"NO:      {no_price}% ({no_price}¢)")
    except Exception as e:
        print(f"Error fetching probabilities for {ticker}: {e}")

# =========================================================
# RUNNER (for testing your functions)
# =========================================================

if __name__ == "__main__":
    try:
        kalshi = get_initialized_client()
        print("Client initialized.\n")
        
        # Test: Specific Trump/Zelensky meeting market
        get_market_probability(kalshi, "KXTRUMPMEET-26JAN-VZEL")
        
        get_series_outcomes(kalshi, "KXTRUMPMEET") 

    except Exception as e:
        print(f"Error: {e}")
