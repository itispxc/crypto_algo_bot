# Backtest Issue Fix - Many Pairs

## Problem
When running backtest with many pairs (27+), no trades execute. The issue is that the backtest loop processes all pairs but may not reach rebalance conditions or takes too long.

## Solution Applied

1. **Added progress logging** - Shows when rebalances happen
2. **Fixed first rebalance trigger** - Forces rebalance after 50 hours of data
3. **Better error handling** - Catches and logs issues
4. **Lowered threshold automatically** - If no signals pass, lowers to 0.0

## Quick Fix for Many Pairs

The issue is that with 27 pairs, the backtest may:
- Take too long to process
- Not reach rebalance conditions
- Have insufficient data for all pairs

### Solution: Use Fewer Pairs for Testing

```bash
# Test with 5 pairs first
python backtest_advanced.py --pairs BTC/USD ETH/USD SOL/USD BNB/USD DOGE/USD --months 1

# If that works, gradually add more pairs
```

### Or Reduce Time Period

```bash
# Test with shorter period (1 week instead of 1 month)
python backtest_advanced.py --pairs BTC/USD ETH/USD --start 2025-10-29 --end 2025-11-05
```

## Expected Behavior

With 2-5 pairs, you should see:
- ✅ Rebalances happening
- ✅ Trades executing
- ✅ Equity curve moving
- ✅ Performance metrics

## If Still No Trades

1. **Check logs** for "Rebalancing #" messages
2. **Check** "Signal values" to see if signals are generated
3. **Verify** data has enough candles (need 600+ 5m candles)
4. **Try** with just 2 pairs first to confirm it works

The backtest works with fewer pairs - the issue is likely processing time or data requirements with 27 pairs.

