#!/usr/bin/env python3
"""
Debug script to test backtest with detailed logging.
"""
import logging
from datetime import datetime, timedelta
from backtest_advanced import run_backtest_advanced

# Set logging to INFO to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("=" * 80)
print("RUNNING BACKTEST WITH DEBUGGING")
print("=" * 80)
print()

# Run a short backtest (1 month)
results = run_backtest_advanced(
    pairs=['BTC/USD', 'ETH/USD'],
    months=1
)

if results:
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(f"Initial Balance: ${results['initial_balance']:,.2f}")
    print(f"Final Balance: ${results['final_balance']:,.2f}")
    print(f"Total Return: ${results['total_return']:,.2f} ({results['total_return_pct']:.2f}%)")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Win Rate: {results['win_rate']:.2f}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.3f}")
    print("=" * 80)
    
    if results['total_trades'] == 0:
        print("\n⚠️  WARNING: No trades executed!")
        print("Check the logs above to see why trades weren't executed.")
    else:
        print(f"\n✅ Successfully executed {results['total_trades']} trades!")

