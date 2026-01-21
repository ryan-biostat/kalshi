import time
import csv
import os
from datetime import datetime
from my_kalshi_tools import get_initialized_client

def monitor_ticker(client, ticker, interval=60):
    """
    Monitors a specific market ticker, printing updates and logging to CSV.
    """
    # Ensure log directory exists
    log_dir = "monitor_logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    print(f"Starting monitor for: {ticker}")
    print(f"Update interval: {interval} seconds")
    
    # Initialize CSV file path inside the log directory
    log_file = os.path.join(log_dir, f"{ticker}_log.csv")
    print(f"Logging to: {log_file}\n")
    
    file_exists = os.path.isfile(log_file)
    
    with open(log_file, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Price (Cents)", "Volume", "Change"])
            
    last_price = None
    
    try:
        while True:
            # Fetch Data
            try:
                data = client.get_market(ticker)
                market = data.get('market', {})
                current_price = market.get('yes_ask')
                volume = market.get('volume')
                title = market.get('title')
            except Exception as e:
                print(f"Error fetching data: {e}")
                time.sleep(interval)
                continue

            # Calculate Change
            change = 0
            if last_price is not None and current_price is not None:
                change = current_price - last_price
            
            # Timestamp
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Extract side from ticker (the part after the last '-')
            side = ticker.split('-')[-1]
            
            # Console Output
            change_str = f"({change:+d})" if last_price is not None else ""
            print(f"[{now}] {title} [{side}] | Price: {current_price}¢ {change_str} | Vol: {volume}")
            
            # File Log
            with open(log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([now, current_price, volume, change])
            
            # Update state
            last_price = current_price
            
            # Wait
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nMonitor stopped by user.")

if __name__ == "__main__":
    try:
        kalshi = get_initialized_client()
        
        # Default Ticker: Wisconsin to win (from our previous search)
        # You can change this to any ticker you found earlier
        TARGET_TICKER = "KXNCAAMBGAME-26JAN22WISPSU-WIS"
        
        # Monitor every 10 seconds for testing purposes (usually 60 is good)
        monitor_ticker(kalshi, TARGET_TICKER, interval=10)
        
    except Exception as e:
        print(f"Error: {e}")
