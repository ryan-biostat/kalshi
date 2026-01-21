import time
import json
import os
from datetime import datetime
from my_kalshi_tools import get_initialized_client

def monitor_series(client, series_ticker, interval=60, search_term=None):
    """
    Monitors a series and logs outcomes to a JSONL file.
    Optional search_term filters for a specific matchup (e.g. 'SLABAR').
    """
    # Ensure log directory exists
    log_dir = "monitor_logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    filter_desc = f" (filtered by: {search_term})" if search_term else ""
    print(f"Initializing JSONL monitor for series: {series_ticker}{filter_desc}")
    print(f"Update interval: {interval} seconds")
    
    # Update log file name if filtered
    suffix = f"_{search_term}" if search_term else ""
    log_file = os.path.join(log_dir, f"{series_ticker}{suffix}_monitor.jsonl")
    print(f"Logging to: {log_file}\n")

    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            current_data = []
            my_cursor = None
            while True:
                response = client.get_markets(series_ticker=series_ticker, limit=100, cursor=my_cursor)
                batch = response.get('markets', [])
                
                # Apply filter if provided
                if search_term:
                    batch = [m for m in batch if search_term.upper() in m.get('ticker', '').upper()]
                
                current_data.extend(batch)
                my_cursor = response.get('cursor')
                if not my_cursor or not batch:
                    break
            
            # Build the record for this timestamp
            # We map Ticker -> {Title, Price}
            # This preserves metadata so you don't lose the Title if it changes
            snapshot = {
                "timestamp": timestamp,
                "markets": {}
            }
            
            # For console display
            display_list = []

            for m in current_data:
                ticker = m.get('ticker')
                title = m.get('title')
                ask = m.get('yes_ask')
                bid = m.get('yes_bid')
                volume = m.get('volume')
                
                # Treat None as 0
                if ask is None: ask = 0
                if bid is None: bid = 0
                
                # Filter out settled markets (Ask >= 100 or Bid >= 100)
                if ask >= 100 or bid >= 100:
                    continue

                snapshot["markets"][ticker] = {
                    "title": title,
                    "ask": ask,
                    "bid": bid,
                    "volume": volume
                }
                
                # Add to display list if relevant (Ask > 1 cent)
                if ask > 1:
                    display_list.append((title, bid, ask, volume, ticker))

            # Write to JSONL
            with open(log_file, 'a') as f:
                f.write(json.dumps(snapshot) + "\n")
            
            # Sort display list by ASK price descending
            display_list.sort(key=lambda x: x[2], reverse=True)
            
            # Print Summary (Top 5)
            summary_parts = []
            for title, bid, ask, vol, ticker in display_list[:5]:
                # Extract the suffix (e.g. 'BAR' from '...-SLABAR-BAR')
                suffix = ticker.split('-')[-1]
                # Format: [CODE] Bid/Ask (Vol)
                summary_parts.append(f"[{suffix}] {bid}/{ask}¢ (v{vol})")
            
            summary_str = " | ".join(summary_parts)
            print(f"[{timestamp}] {summary_str} ...")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nMonitor stopped.")

if __name__ == "__main__":
    try:
        kalshi = get_initialized_client()
        # Monitor specific game: Stoke City vs Middlesbrough (EFL)
        # 2 second refresh rate
        monitor_series(kalshi, "KXEUROCUPGAME", interval=2, search_term="NEPMAN")
    except Exception as e:
        print(f"Error: {e}")
