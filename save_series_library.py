import os
import sys
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

# Add path for clients
sys.path.append(os.path.join(os.path.dirname(__file__), 'kalshi-starter-code-python'))
from clients import KalshiHttpClient, Environment

def get_initialized_client():
    load_dotenv()
    env = Environment.PROD 
    KEYID = os.getenv('PROD_KEYID')
    KEYFILE = os.getenv('PROD_KEYFILE')
    with open(KEYFILE, "rb") as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None)
    return KalshiHttpClient(key_id=KEYID, private_key=private_key, environment=env)

def save_all_series():
    client = get_initialized_client()
    print("Fetching series library...")
    
    all_series = []
    my_cursor = None
    
    while True:
        # Use generic get for series pagination
        params = {"limit": 1000}
        if my_cursor:
            params["cursor"] = my_cursor
            
        data = client.get("/trade-api/v2/series", params)
        series_batch = data.get('series', [])
        all_series.extend(series_batch)
        
        my_cursor = data.get('cursor')
        print(f"Retrieved {len(all_series)} series so far...")
        
        if not my_cursor or not series_batch:
            break

    # Sort alphabetically by ticker
    all_series.sort(key=lambda x: x.get('ticker', ''))

    # Save to file
    with open("kalshi_series_library.txt", "w") as f:
        f.write("# KALSHI SERIES LIBRARY\n")
        f.write(f"# Last Updated: 2026-01-21\n")
        f.write(f"# Total Series: {len(all_series)}\n\n")
        for s in all_series:
            ticker = s.get('ticker', 'N/A')
            title = s.get('title', 'N/A')
            f.write(f"[{ticker}] - {title}\n")

    print(f"\nSUCCESS: Saved {len(all_series)} series to kalshi_series_library.txt")

if __name__ == "__main__":
    save_all_series()
