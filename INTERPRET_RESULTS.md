# Interpreting 20-Day Optimization Results

## Your Current Result

```
Return: 17.98%
Sharpe: 30.631
Trades: 97
```

### Analysis

**✅ Excellent Sharpe Ratio (30.631)**
- This is extremely high - indicates very consistent returns
- Sharpe > 1.5 is good, > 2.0 is excellent

**✅ Good Return (17.98% in 20 days)**
- Strong performance for a 20-day period

**⚠️ High Trade Count (97 trades)**
- 97 trades in 20 days = ~4.9 trades per day
- With 0.2% fees per trade (0.1% buy + 0.1% sell):
  - Total fees: 97 × 0.2% = 19.4%
  - Net return after fees: 17.98% - 19.4% = **-1.42%** (loss!)

### Trade Efficiency

- **Return per trade**: 17.98% / 97 = **0.185% per trade**
- **Fees per trade**: 0.2%
- **Net per trade**: -0.015% (losing money on fees!)

### The Problem

You're **overtrading**! The fees are eating into your profits.

## Optimization Goal

Find the **sweet spot** where:
- ✅ Sharpe > 1.5
- ✅ Return > 5%
- ✅ Trade count: **8-20 per 20 days** (not 97!)
- ✅ Return per trade > 0.5%

## What to Look For in Results

### Good Configuration:
```
Avg Sharpe: 2.0-3.0
Avg Return: 8-12%
Avg Trades: 10-15 per 20 days
Return per Trade: > 0.5%
```

### Bad Configuration:
```
Avg Sharpe: 30.0 (too high = suspicious)
Avg Return: 18%
Avg Trades: 97 (TOO MANY!)
Return per Trade: < 0.2%
```

## Next Steps

1. **Run full optimization** to find better configurations:
   ```bash
   python optimize_20day.py --periods 5
   ```

2. **Look for configurations with:**
   - Lower trade count (8-20)
   - Still good Sharpe (> 1.5)
   - Still good return (> 5%)
   - Higher return per trade

3. **The optimization will show:**
   - Best configuration by composite score
   - Trade count analysis
   - Performance by trade count range

4. **Update config.yaml** with the best configuration that balances:
   - Sharpe ratio
   - Return
   - Trade count (not too many!)

## Key Insight

**More trades ≠ Better performance**

The optimal strategy usually has:
- **8-15 trades per 20 days** (not 97!)
- **Higher return per trade** (> 0.5%)
- **Still good Sharpe** (> 1.5)

This is what the optimization will find for you!

