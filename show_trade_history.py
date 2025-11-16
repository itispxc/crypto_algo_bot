"""
Show trade history from Roostoo exchange.
"""
import yaml
import os
import sys
from datetime import datetime
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_client import DataClient

def format_trade(order: Dict) -> str:
    """Format a single trade for display."""
    pair = order.get('Pair', 'N/A')
    side = order.get('Side', 'N/A')
    qty = order.get('Quantity', 0)
    price = order.get('Price', 0)
    status = order.get('Status', 'N/A')
    order_id = order.get('OrderID', 'N/A')
    timestamp = order.get('Timestamp', order.get('Time', 'N/A'))
    
    # Try to parse timestamp
    if isinstance(timestamp, (int, float)):
        try:
            dt = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
            time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            time_str = str(timestamp)
    else:
        time_str = str(timestamp)
    
    value = qty * price if qty and price else 0
    
    return f"{time_str} | {side:4s} | {pair:10s} | {qty:12.6f} @ ${price:10.2f} | ${value:10.2f} | {status:10s} | ID: {order_id}"

def main():
    config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    client = DataClient(config)
    
    print("=" * 120)
    print("TRADE HISTORY")
    print("=" * 120)
    
    # Get all orders (not just pending)
    try:
        # Query for ZEC/USD orders
        zec_orders = client.client.query_order(pair="ZEC/USD", pending_only=False, limit=100)
        
        # Query for BTC/USD orders  
        btc_orders = client.client.query_order(pair="BTC/USD", pending_only=False, limit=100)
        
        all_orders = []
        
        if zec_orders.get('Success') and zec_orders.get('OrderMatched'):
            all_orders.extend(zec_orders['OrderMatched'])
        
        if btc_orders.get('Success') and btc_orders.get('OrderMatched'):
            all_orders.extend(btc_orders['OrderMatched'])
        
        if not all_orders:
            print("No trades found.")
            return
        
        # Sort by timestamp (newest first)
        all_orders.sort(key=lambda x: x.get('Timestamp', x.get('Time', 0)), reverse=True)
        
        print(f"\nFound {len(all_orders)} trades:\n")
        print(f"{'Time':20s} | {'Side':4s} | {'Pair':10s} | {'Quantity':12s} @ {'Price':10s} | {'Value':10s} | {'Status':10s} | Order ID")
        print("-" * 120)
        
        for order in all_orders:
            print(format_trade(order))
        
        # Summary
        buy_orders = [o for o in all_orders if o.get('Side', '').upper() == 'BUY']
        sell_orders = [o for o in all_orders if o.get('Side', '').upper() == 'SELL']
        
        print("\n" + "=" * 120)
        print("SUMMARY")
        print("=" * 120)
        print(f"Total trades: {len(all_orders)}")
        print(f"Buy orders: {len(buy_orders)}")
        print(f"Sell orders: {len(sell_orders)}")
        
        if buy_orders:
            total_buy_value = sum(o.get('Quantity', 0) * o.get('Price', 0) for o in buy_orders)
            print(f"Total buy value: ${total_buy_value:,.2f}")
        
        if sell_orders:
            total_sell_value = sum(o.get('Quantity', 0) * o.get('Price', 0) for o in sell_orders)
            print(f"Total sell value: ${total_sell_value:,.2f}")
            if buy_orders:
                profit = total_sell_value - total_buy_value
                profit_pct = (profit / total_buy_value * 100) if total_buy_value > 0 else 0
                print(f"Net profit: ${profit:,.2f} ({profit_pct:.2f}%)")
        
    except Exception as e:
        print(f"Error fetching trade history: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

