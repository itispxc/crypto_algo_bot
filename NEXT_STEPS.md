# What To Do Now - Step by Step Guide

## Current Status
You've started the 20-day optimization. Here's what to do:

## Step 1: Let Optimization Complete ⏳

If the optimization is still running, **let it finish**. It will:
- Test multiple parameter combinations
- Find optimal trade count (8-20 trades)
- Rank configurations by Sharpe + Return + Consistency

**Expected time:**
- Quick optimization: 10-15 minutes
- Full optimization: 30-45 minutes

## Step 2: Review Results 📊

Once complete, you'll see:
- `optimization_20day_results.csv` - All results
- Console output showing top configurations

**Look for:**
- ✅ Configurations with 8-20 trades per 20 days
- ✅ Sharpe > 1.5
- ✅ Return > 5%
- ✅ High composite score

## Step 3: Update Config File ⚙️

Edit `config/config.yaml` with the best configuration:

```yaml
signals:
  score_threshold: [best_value]  # e.g., 0.02
  top_k_normal: [best_value]     # e.g., 6
  hysteresis_weight_change: [best_value]  # e.g., 0.05

sizing:
  cash_buffer_normal: [best_value]  # e.g., 0.10
```

## Step 4: Test on Competition Dates 🎯

Test the optimized config on actual competition period:

```bash
python -c "
from backtest_advanced import run_backtest_advanced
import logging
logging.basicConfig(level=logging.WARNING)

result = run_backtest_advanced(
    pairs=['BTC/USD', 'ETH/USD', 'SOL/USD'],
    start_date='2024-11-10',
    end_date='2024-11-30',
    random_seed=42
)
print(f'Return: {result[\"total_return_pct\"]:.2f}%')
print(f'Sharpe: {result[\"sharpe_ratio\"]:.3f}')
print(f'Trades: {result[\"total_trades\"]}')
print(f'Fees: \${result.get(\"total_fees\", 0):.2f}')
print(f'Net Return: {result[\"total_return_pct\"]:.2f}% - fees')
"
```

## Step 5: Verify Trade Count ✅

**Check:**
- ✅ Trade count: 8-20 per 20 days (not 50+)
- ✅ Sharpe > 1.5
- ✅ Return > 5%
- ✅ Fees < 5% of return

## If Optimization Not Running Yet

Run the quick optimization:

```bash
python QUICK_20DAY_OPTIMIZE.py
```

Or full optimization:

```bash
python optimize_20day.py --pairs BTC/USD ETH/USD SOL/USD --periods 5
```

## Quick Checklist

- [ ] Optimization complete (or running)
- [ ] Reviewed results CSV file
- [ ] Found configuration with 8-20 trades
- [ ] Updated `config/config.yaml`
- [ ] Tested on competition dates (Nov 10-30)
- [ ] Verified trade count is reasonable
- [ ] Ready for competition!

## Need Help?

- **Results don't make sense?** Check `INTERPRET_RESULTS.md`
- **Want to understand metrics?** See `20DAY_COMPETITION_GUIDE.md`
- **Still too many trades?** Increase `hysteresis_weight_change` to 0.10

Good luck! 🚀

