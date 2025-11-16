"""
Show current open positions.
"""
import yaml
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_client import DataClient

def main():
    config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    client = DataClient(config)
    
    print("=" * 80)
    print("CURRENT OPEN POSITIONS")
    print("=" * 80)
    
    state = client.get_positions()
    
    print(f"\nCash: ${state.cash_usd:,.2f}")
    print(f"Total Equity: ${state.equity:,.2f}")
    print(f"\nPositions:")
    print("-" * 80)
    
    if not state.positions:
        print("No open positions.")
    else:
        for pair, position in state.positions.items():
            if position.quantity > 0:
                # Get current price
                snapshot = client.get_snapshot(pair)
                if snapshot:
                    current_price = snapshot.price
                    entry_price = position.avg_price
                    profit_pct = ((current_price - entry_price) / entry_price) * 100
                    value = position.quantity * current_price
                    
                    print(f"\n{pair}:")
                    print(f"  Quantity: {position.quantity:.6f}")
                    print(f"  Entry Price: ${entry_price:.2f}")
                    print(f"  Current Price: ${current_price:.2f}")
                    print(f"  Profit/Loss: {profit_pct:+.2f}%")
                    print(f"  Current Value: ${value:,.2f}")
                else:
                    print(f"\n{pair}:")
                    print(f"  Quantity: {position.quantity:.6f}")
                    print(f"  Entry Price: ${position.avg_price:.2f}")
                    print(f"  (Could not fetch current price)")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

