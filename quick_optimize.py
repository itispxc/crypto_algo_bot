#!/usr/bin/env python3
"""
Quick optimization script - tests fewer combinations for faster results.
"""
from optimize_backtest import BacktestOptimizer

if __name__ == "__main__":
    print("=" * 80)
    print("QUICK OPTIMIZATION - Testing Key Parameters")
    print("=" * 80)
    print()
    print("This will test 12 combinations to find optimal settings.")
    print("For full optimization, use: python optimize_backtest.py")
    print()
    
    optimizer = BacktestOptimizer()
    
    # Test key parameters only
    param_ranges = {
        'score_threshold': [0.01, 0.02, 0.03],  # 3 values
        'top_k_normal': [6, 8],  # 2 values
        'cash_buffer_normal': [0.10, 0.15],  # 2 values
        # Total: 3 × 2 × 2 = 12 combinations
    }
    
    results_df = optimizer.run_optimization(
        pairs=['BTC/USD', 'ETH/USD', 'SOL/USD', 'BNB/USD'],
        months=1,
        param_ranges=param_ranges,
        max_tests=12,
        random_seed=42
    )
    
    optimizer.print_results(results_df, top_n=5)
    optimizer.save_results(results_df, "quick_optimization_results.csv")
    
    if len(results_df) > 0:
        best = results_df.iloc[0]
        print("\n" + "=" * 80)
        print("RECOMMENDED CONFIGURATION")
        print("=" * 80)
        print(f"\nUpdate config/config.yaml with:")
        print(f"  signals:")
        print(f"    score_threshold: {best.get('score_threshold', 0.02)}")
        print(f"    top_k_normal: {best.get('top_k_normal', 8)}")
        print(f"  sizing:")
        print(f"    cash_buffer_normal: {best.get('cash_buffer_normal', 0.10)}")
        print(f"\nExpected performance:")
        print(f"  Return: {best['total_return_pct']:.2f}%")
        print(f"  Sharpe: {best['sharpe_ratio']:.3f}")
        print(f"  Trades: {int(best['total_trades'])}")
        print("=" * 80)

