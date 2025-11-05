#!/usr/bin/env python3
"""
Interactive backtesting script - TradingView style.
Easy-to-use interface for running backtests with visualization.
"""
import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtest_advanced import run_backtest_advanced
import yaml


def main():
    """Interactive backtest interface."""
    print("=" * 80)
    print("TRADINGVIEW-STYLE BACKTESTING")
    print("=" * 80)
    print()
    
    # Load config for available pairs
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    all_pairs = (config["universe"]["tier1"] + 
                config["universe"]["tier2"] + 
                config["universe"]["tier3"])
    
    print("Available Trading Pairs:")
    print(f"  Tier 1: {', '.join(config['universe']['tier1'][:6])}... ({len(config['universe']['tier1'])} total)")
    print(f"  Tier 2: {', '.join(config['universe']['tier2'][:6])}... ({len(config['universe']['tier2'])} total)")
    print(f"  Tier 3: {', '.join(config['universe']['tier3'])} ({len(config['universe']['tier3'])} total)")
    print()
    
    # Get user input
    print("Backtest Configuration:")
    print()
    
    # Time period
    print("1. Time Period:")
    print("   a) Last month (1 month)")
    print("   b) Last 3 months")
    print("   c) Last 6 months")
    print("   d) Last year (12 months)")
    print("   e) Custom date range")
    
    choice = input("\n   Select option (a-e): ").strip().lower()
    
    months = 0
    years = 0
    start_date = None
    end_date = None
    
    if choice == 'a':
        months = 1
    elif choice == 'b':
        months = 3
    elif choice == 'c':
        months = 6
    elif choice == 'd':
        years = 1
    elif choice == 'e':
        start_str = input("   Start date (YYYY-MM-DD): ").strip()
        end_str = input("   End date (YYYY-MM-DD): ").strip()
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_str, "%Y-%m-%d")
        except:
            print("   Invalid date format, using default (1 month)")
            months = 1
    else:
        months = 1
    
    # Pairs selection
    print("\n2. Trading Pairs:")
    print("   a) Top 5 pairs (BTC, ETH, SOL, BNB, DOGE)")
    print("   b) All Tier 1 pairs")
    print("   c) All pairs (Tier 1 + 2 + 3)")
    print("   d) Custom selection")
    
    pair_choice = input("\n   Select option (a-d): ").strip().lower()
    
    pairs = None
    if pair_choice == 'a':
        pairs = ['BTC/USD', 'ETH/USD', 'SOL/USD', 'BNB/USD', 'DOGE/USD']
    elif pair_choice == 'b':
        pairs = config['universe']['tier1']
    elif pair_choice == 'c':
        print("   ⚠️  WARNING: Testing with all pairs may take a long time and may not execute trades.")
        print("   Consider using option 'b' (Tier 1 only) for better results.")
        confirm = input("   Continue with all pairs? (y/n): ").strip().lower()
        if confirm == 'y':
            pairs = all_pairs
        else:
            pairs = config['universe']['tier1']
            print(f"   Using Tier 1 pairs instead ({len(pairs)} pairs)")
    elif pair_choice == 'd':
        print(f"\n   Available pairs: {', '.join(all_pairs[:20])}...")
        pair_input = input("   Enter pairs (comma-separated, e.g., BTC/USD,ETH/USD): ").strip()
        pairs = [p.strip() for p in pair_input.split(',')]
    else:
        pairs = ['BTC/USD', 'ETH/USD', 'SOL/USD', 'BNB/USD', 'DOGE/USD']
    
    print(f"\n   Selected {len(pairs)} pairs")
    
    # Run backtest
    print("\n" + "=" * 80)
    print("Starting Backtest...")
    print("=" * 80)
    print()
    
    try:
        results = run_backtest_advanced(
            pairs=pairs,
            start_date=start_date.strftime("%Y-%m-%d") if start_date else None,
            end_date=end_date.strftime("%Y-%m-%d") if end_date else None,
            months=months,
            years=years
        )
        
        print("\n" + "=" * 80)
        print("Backtest Complete!")
        print("=" * 80)
        print(f"\nCharts saved to: backtest_results.png")
        print("\nYou can now:")
        print("  1. View the charts in backtest_results.png")
        print("  2. Run another backtest with different parameters")
        print("  3. Adjust strategy parameters in config/config.yaml")
        
    except Exception as e:
        print(f"\nError during backtest: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

