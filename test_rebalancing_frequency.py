#!/usr/bin/env python3
"""
Test different rebalancing frequencies.
Note: Currently rebalances every 30 minutes. This script tests different hysteresis
values which effectively changes how often trades execute.
"""
from optimize_comprehensive import ComprehensiveOptimizer
import logging

logging.basicConfig(level=logging.WARNING)

print("=" * 80)
print("TESTING REBALANCING FREQUENCY")
print("=" * 80)
print()
print("Current: Rebalances every 30 minutes")
print("Testing via hysteresis (weight change threshold)")
print()

optimizer = ComprehensiveOptimizer()

# Test different hysteresis values
# Lower = More frequent rebalancing (smaller changes trigger trades)
# Higher = Less frequent rebalancing (only large changes trigger trades)

results = optimizer.optimize_rebalancing_frequency(
    pairs=['BTC/USD', 'ETH/USD', 'SOL/USD'],
    base_params={
        'score_threshold': 0.02,
        'top_k_normal': 6,
        'cash_buffer_normal': 0.10,
    },
    months=1,
    random_seed=42
)

if len(results) > 0:
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    # Sort by Sharpe
    results = results.sort_values('sharpe_ratio', ascending=False)
    
    print("\nRanked by Sharpe Ratio:")
    for idx, row in results.iterrows():
        print(f"\nHysteresis: {row['hysteresis']:.3f} ({row['hysteresis']*100:.1f}% threshold)")
        print(f"  Trades: {row['total_trades']:.0f}")
        print(f"  Sharpe: {row['sharpe_ratio']:.3f}")
        print(f"  Return: {row['total_return_pct']:.2f}%")
        print(f"  Fees: ${row['total_fees']:.2f}")
        print(f"  Return per trade: {row.get('return_per_trade', 0):.2f}%")
    
    # Find optimal
    best = results.iloc[0]
    print(f"\n{'='*80}")
    print("RECOMMENDATION")
    print(f"{'='*80}")
    print(f"Optimal hysteresis: {best['hysteresis']:.3f}")
    print(f"This gives: {best['total_trades']:.0f} trades, Sharpe {best['sharpe_ratio']:.3f}")
    print(f"\nUpdate config.yaml:")
    print(f"  signals:")
    print(f"    hysteresis_weight_change: {best['hysteresis']:.3f}")
    
    results.to_csv("rebalancing_frequency_results.csv", index=False)
    print(f"\nResults saved to: rebalancing_frequency_results.csv")

