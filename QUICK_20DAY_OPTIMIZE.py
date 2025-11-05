#!/usr/bin/env python3
"""
Quick 20-day optimization - faster version for testing.
Tests fewer combinations to find optimal trade count quickly.
"""
from optimize_20day import Optimizer20Day
import logging
import sys
import os

# Suppress all logging during optimization
logging.basicConfig(level=logging.ERROR)
logging.getLogger().setLevel(logging.ERROR)

# Redirect stdout to reduce output during backtests
class QuietOutput:
    def __init__(self):
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
    
    def __enter__(self):
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        return self
    
    def __exit__(self, *args):
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

print("=" * 80)
print("QUICK 20-DAY OPTIMIZATION")
print("=" * 80)
print()
print("Testing strategy on random 20-day periods")
print("Finding optimal trade count for highest Sharpe and profit")
print()

optimizer = Optimizer20Day()

# Test key parameters only (faster)
from itertools import product

param_ranges = {
    'score_threshold': [0.01, 0.02, 0.03],
    'top_k_normal': [4, 6, 8],
    'cash_buffer_normal': [0.10, 0.15],
    'hysteresis': [0.02, 0.03, 0.05],
}

# Generate combinations
param_names = list(param_ranges.keys())
param_values = list(param_ranges.values())
all_combinations = list(product(*param_values))

print(f"Testing {len(all_combinations)} combinations...")
print(f"Each on 3 random 20-day periods")
print()

results = []

for i, combo in enumerate(all_combinations, 1):
    params = dict(zip(param_names, combo))
    
    print(f"Test {i}/{len(all_combinations)}: {params}", end=" ... ")
    
    # Test on 3 random periods
    period_results = optimizer.test_random_20day_periods(
        pairs=['BTC/USD', 'ETH/USD', 'SOL/USD'],
        config_params=params,
        num_periods=3,
        random_seed=42
    )
    
    if len(period_results) > 0:
        agg_result = {
            **params,
            'avg_sharpe': period_results['sharpe_ratio'].mean(),
            'avg_return': period_results['total_return_pct'].mean(),
            'avg_trades': period_results['total_trades'].mean(),
            'avg_win_rate': period_results['win_rate'].mean(),
            'std_sharpe': period_results['sharpe_ratio'].std(),
        }
        
        agg_result['composite_score'] = (
            0.5 * agg_result['avg_sharpe'] +
            0.3 * (agg_result['avg_return'] / 10.0) +
            0.2 * (1.0 / (1.0 + agg_result['std_sharpe']))
        )
        
        results.append(agg_result)
        
        print(f"✅ Sharpe: {agg_result['avg_sharpe']:.3f}, "
              f"Return: {agg_result['avg_return']:.2f}%, "
              f"Trades: {agg_result['avg_trades']:.1f}")
    else:
        print("❌")

import pandas as pd
results_df = pd.DataFrame(results)

if len(results_df) > 0:
    results_df = results_df.sort_values('composite_score', ascending=False)
    
    print(f"\n{'='*80}")
    print("TOP 5 CONFIGURATIONS")
    print(f"{'='*80}\n")
    
    for idx, (_, row) in enumerate(results_df.head(5).iterrows(), 1):
        print(f"Rank {idx}:")
        print(f"  Threshold: {row['score_threshold']}, "
              f"Top K: {row['top_k_normal']}, "
              f"Buffer: {row['cash_buffer_normal']}, "
              f"Hyst: {row['hysteresis']}")
        print(f"  Sharpe: {row['avg_sharpe']:.3f}, "
              f"Return: {row['avg_return']:.2f}%, "
              f"Trades: {row['avg_trades']:.1f}")
        print()
    
    best = results_df.iloc[0]
    print(f"{'='*80}")
    print("BEST CONFIGURATION:")
    print(f"{'='*80}")
    print(f"  score_threshold: {best['score_threshold']}")
    print(f"  top_k_normal: {int(best['top_k_normal'])}")
    print(f"  cash_buffer_normal: {best['cash_buffer_normal']}")
    print(f"  hysteresis_weight_change: {best['hysteresis']}")
    print(f"\n  Expected: {best['avg_trades']:.1f} trades, "
          f"Sharpe {best['avg_sharpe']:.3f}, "
          f"Return {best['avg_return']:.2f}%")
    
    results_df.to_csv("quick_20day_results.csv", index=False)
    print(f"\nResults saved to: quick_20day_results.csv")

