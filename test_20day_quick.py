#!/usr/bin/env python3
"""
Quick test of 20-day optimization - tests just 2 combinations on 1 period each.
Use this to verify everything works before running full optimization.
"""
from optimize_20day import Optimizer20Day
import logging

logging.basicConfig(level=logging.ERROR)
logging.getLogger().setLevel(logging.ERROR)

print("=" * 80)
print("QUICK TEST - 20-DAY OPTIMIZATION")
print("=" * 80)
print()
print("Testing 2 parameter combinations on 1 random 20-day period each")
print("This should complete in 1-2 minutes")
print()

optimizer = Optimizer20Day()

# Test just 2 combinations
test_params = [
    {'score_threshold': 0.02, 'top_k_normal': 6, 'cash_buffer_normal': 0.10, 'hysteresis': 0.03},
    {'score_threshold': 0.01, 'top_k_normal': 8, 'cash_buffer_normal': 0.10, 'hysteresis': 0.02},
]

results = []

for i, params in enumerate(test_params, 1):
    print(f"Test {i}/{len(test_params)}: {params}")
    
    period_results = optimizer.test_random_20day_periods(
        pairs=['BTC/USD', 'ETH/USD'],
        config_params=params,
        num_periods=1,
        random_seed=42
    )
    
    if len(period_results) > 0:
        result = period_results.iloc[0]
        results.append({
            **params,
            'sharpe': result['sharpe_ratio'],
            'return': result['total_return_pct'],
            'trades': result['total_trades'],
        })
        print(f"  ✅ Sharpe: {result['sharpe_ratio']:.3f}, Return: {result['total_return_pct']:.2f}%, Trades: {result['total_trades']}")
    else:
        print("  ❌ Failed")
    print()

if results:
    print("=" * 80)
    print("TEST COMPLETE - System is working!")
    print("=" * 80)
    print()
    print("Now you can run:")
    print("  python QUICK_20DAY_OPTIMIZE.py  # Quick optimization (54 combinations)")
    print("  python optimize_20day.py        # Full optimization (30 combinations)")
else:
    print("❌ Test failed - check errors above")

