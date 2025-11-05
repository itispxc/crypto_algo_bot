#!/usr/bin/env python3
"""
Quick backtest with visualization - simple one-liner.
"""
from backtest_advanced import run_backtest_advanced

if __name__ == "__main__":
    print("Running quick 1-month backtest...")
    print("This will generate TradingView-style charts with performance metrics.\n")
    
    # Run backtest for last month with top 5 pairs
    # Using fixed seed=42 for reproducible results
    results = run_backtest_advanced(
        pairs=['BTC/USD', 'ETH/USD', 'SOL/USD', 'BNB/USD', 'DOGE/USD'],
        months=1,
        random_seed=42  # Fixed seed for reproducibility
    )
    
    if results:
        print("\n✅ Backtest complete!")
        print(f"📊 Charts saved to: backtest_results.png")
        print(f"📈 Return: {results['total_return_pct']:.2f}%")
        print(f"📉 Sharpe: {results['sharpe_ratio']:.3f}")
        print(f"📉 Max DD: {results['max_drawdown_pct']:.2f}%")

