# Backtest Reproducibility

## ✅ Fixed!

The backtest now produces **identical results** when run multiple times with the same parameters.

## What Was Fixed

The issue was that synthetic data generation used random numbers without a fixed seed, causing different results each run.

### Solution Applied

1. **Fixed Random Seed**: Default seed of `42` ensures reproducible results
2. **Pair-Specific Seeds**: Each pair gets a deterministic seed based on its name + global seed
3. **Consistent Data**: Same parameters always generate same price data

## How It Works

```python
# Same seed = same results
results1 = run_backtest_advanced(pairs=['BTC/USD'], months=1, random_seed=42)
results2 = run_backtest_advanced(pairs=['BTC/USD'], months=1, random_seed=42)
# results1 and results2 will be identical
```

## Using Different Seeds

If you want different scenarios:

```python
# Scenario 1
results1 = run_backtest_advanced(pairs=['BTC/USD'], months=1, random_seed=42)

# Scenario 2 (different market conditions)
results2 = run_backtest_advanced(pairs=['BTC/USD'], months=1, random_seed=123)

# Scenario 3 (another variation)
results3 = run_backtest_advanced(pairs=['BTC/USD'], months=1, random_seed=999)
```

## Command Line

```bash
# Reproducible (default seed=42)
python backtest_advanced.py --pairs BTC/USD ETH/USD --months 1

# Different scenario
python backtest_advanced.py --pairs BTC/USD ETH/USD --months 1 --seed 123
```

## Testing Reproducibility

Run the same backtest twice - you should get **identical results**:

```bash
python quick_backtest.py
# Note the results

python quick_backtest.py
# Results should be exactly the same!
```

## Why This Matters

1. **Consistent Testing**: Compare strategy changes fairly
2. **Debugging**: Reproduce issues reliably
3. **Documentation**: Share exact results with team
4. **Validation**: Verify fixes produce expected results

## Note on Real Data

When using **real historical data** (from CSV or API), reproducibility is automatic - the same data file always produces the same results.

The seed only affects **synthetic data generation** used for demonstration/testing.

---

**Your backtests are now reproducible!** 🎯

Run the same test twice and you'll get identical results.

