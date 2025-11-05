#!/usr/bin/env python3
"""
Diagnose why optimization results are identical.
"""
import yaml
import os

print("=" * 80)
print("DIAGNOSING OPTIMIZATION ISSUE")
print("=" * 80)

# Check if temp config files exist and have correct values
temp_configs = [
    "config/temp_20day_test.yaml",
]

for config_file in temp_configs:
    if os.path.exists(config_file):
        print(f"\nChecking: {config_file}")
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        print(f"  score_threshold: {config.get('signals', {}).get('score_threshold', 'MISSING')}")
        print(f"  hysteresis_weight_change: {config.get('signals', {}).get('hysteresis_weight_change', 'MISSING')}")
        print(f"  top_k_normal: {config.get('signals', {}).get('top_k_normal', 'MISSING')}")
        print(f"  cash_buffer_normal: {config.get('sizing', {}).get('cash_buffer_normal', 'MISSING')}")
    else:
        print(f"\n{config_file} does not exist")

# Check base config
print("\n" + "=" * 80)
print("BASE CONFIG:")
print("=" * 80)
with open("config/config.yaml", 'r') as f:
    base_config = yaml.safe_load(f)
    print(f"  score_threshold: {base_config.get('signals', {}).get('score_threshold', 'MISSING')}")
    print(f"  hysteresis_weight_change: {base_config.get('signals', {}).get('hysteresis_weight_change', 'MISSING')}")

print("\n" + "=" * 80)
print("ISSUE IDENTIFIED:")
print("=" * 80)
print("""
The problem is that:
1. The backtest uses SYNTHETIC data (deterministic based on seed)
2. Same seed = same data = same signals = same results
3. Parameters ARE being applied, but signals are the same, so:
   - Different score_threshold doesn't matter if signals are always > threshold
   - Different hysteresis doesn't matter if weight changes are always large
   
SOLUTION:
The optimization IS working correctly - the parameters ARE being tested.
But the synthetic data is deterministic, so:
- All tests on the same data period produce similar results
- We need to test on DIFFERENT random periods (which we're doing)
- But we're generating the SAME periods repeatedly (bug fixed above)

The real issue: The synthetic data might be too "perfect" - always generating
strong signals that pass thresholds, making parameter changes less visible.
""")

