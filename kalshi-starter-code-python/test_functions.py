import os
import json
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from clients import KalshiHttpClient, Environment

def print_json(data, label):
    print(f"\n--- {label} ---")
    print(json.dumps(data, indent=2))

def main():
    # 1. Load configuration
    load_dotenv()
    # We'll assume PROD since that's what we configured earlier, 
    # but strictly speaking this should match your .env setup.
    env = Environment.PROD 
    
    KEYID = os.getenv('PROD_KEYID')
    KEYFILE = os.getenv('PROD_KEYFILE')

    if not KEYID or not KEYFILE:
        print("Error: PROD_KEYID or PROD_KEYFILE not found in .env")
        return

    # 2. Load Private Key
    try:
        with open(KEYFILE, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )
    except Exception as e:
        print(f"Error loading private key: {e}")
        return

    # 3. Initialize Client
    client = KalshiHttpClient(
        key_id=KEYID,
        private_key=private_key,
        environment=env
    )
    print("Client initialized successfully.")

    # 4. Test: Get Exchange Status
    status = client.get_exchange_status()
    print_json(status, "Exchange Status")

    # 5. Test: Get Markets (Limit 3)
    markets_response = client.get_markets(limit=3)
    print_json(markets_response, "Markets (Limit 3)")

    # Extract a ticker for the next tests
    try:
        # Structure is usually {'markets': [...]} 
        first_market = markets_response.get('markets', [])[0]
        test_ticker = first_market['ticker']
        print(f"\nSelected Ticker for details: {test_ticker}")
    except (IndexError, KeyError):
        print("\nCould not find a market to test details with.")
        return

    # 6. Test: Get Specific Market
    market_detail = client.get_market(test_ticker)
    print_json(market_detail, f"Market Details for {test_ticker}")

    # 7. Test: Get Orderbook
    orderbook = client.get_orderbook(test_ticker, depth=5)
    print_json(orderbook, f"Orderbook for {test_ticker}")

    # 8. Test: Get Positions
    positions = client.get_positions()
    print_json(positions, "My Positions")

    # 9. Test: Get Orders (History)
    orders = client.get_orders(limit=5)
    print_json(orders, "My Recent Orders")

if __name__ == "__main__":
    main()
