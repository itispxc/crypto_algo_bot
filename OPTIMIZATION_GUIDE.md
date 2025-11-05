# Backtest Optimization Guide

## Quick Start

### Basic Optimization
```bash
# Run optimization with default parameters
python optimize_backtest.py

# Test with specific pairs
python optimize_backtest.py --pairs BTC/USD ETH/USD SOL/USD

# Test with 3 months of data
python optimize_backtest.py --months 3

# Limit to 20 tests (faster)
python optimize_backtest.py --max-tests 20
```

## What Gets Optimized

The script tests different combinations of:

1. **Score Threshold** (0.01, 0.02, 0.03)
   - Lower = More trades, more signals
   - Higher = Fewer but better trades

2. **Top K Normal** (4, 6, 8 positions)
   - How many assets to hold in trend markets
   - More positions = More diversification

3. **Cash Buffer** (5%, 10%, 15%)
   - How much cash to keep in reserve
   - Lower = More capital deployed

4. **Hysteresis** (2%, 3%, 5%)
   - Minimum weight change to trigger rebalance
   - Higher = Fewer rebalances, less trading

## Example Output

```
OPTIMIZATION RESULTS - Top 10

Rank 1:
  Parameters:
    score_threshold: 0.02
    top_k_normal: 6
    cash_buffer_normal: 0.10
    hysteresis: 0.03
  Performance:
    Return: 15.23%
    Sharpe: 2.145
    Sortino: 2.876
    Max DD: -3.45%
    Trades: 12
    Win Rate: 66.7%
    Composite Score: 0.923

Rank 2:
  ...
```

## Understanding the Results

### Composite Score
- **60% Sharpe Ratio** + **40% Return**
- Higher is better
- Balances risk-adjusted returns with absolute returns

### Key Metrics to Watch

1. **Sharpe Ratio** (Target: > 1.5)
   - Risk-adjusted return
   - Higher = Better risk-adjusted performance

2. **Total Return** (Target: Positive)
   - Absolute profit
   - Higher = More money made

3. **Total Trades** (Target: Not too many)
   - Number of trades executed
   - Too many = Overtrading
   - Too few = Missing opportunities

4. **Win Rate** (Target: > 50%)
   - Percentage of profitable trades
   - Higher = Better trade selection

5. **Max Drawdown** (Target: < 15%)
   - Worst peak-to-trough decline
   - Lower = Less risk

## Finding the Sweet Spot

### Scenario 1: High Sharpe, Low Trades
- **Look for**: Sharpe > 2.0, Trades < 10
- **Parameters**: Higher threshold (0.03), Higher hysteresis (0.05)
- **Result**: Fewer but better trades

### Scenario 2: High Return, Moderate Trades
- **Look for**: Return > 20%, Trades 10-20
- **Parameters**: Lower threshold (0.01), Lower hysteresis (0.02)
- **Result**: More active trading, higher returns

### Scenario 3: Balanced (Recommended)
- **Look for**: Sharpe > 1.5, Return > 10%, Trades 8-15
- **Parameters**: Medium threshold (0.02), Medium hysteresis (0.03)
- **Result**: Good balance of risk and return

## Custom Optimization

Edit `optimize_backtest.py` to test different ranges:

```python
param_ranges = {
    'score_threshold': [0.01, 0.015, 0.02, 0.025, 0.03],  # More granular
    'top_k_normal': [4, 5, 6, 7, 8, 9, 10],  # More options
    'cash_buffer_normal': [0.05, 0.08, 0.10, 0.12, 0.15],
    'hysteresis': [0.01, 0.02, 0.03, 0.04, 0.05],
}
```

## After Optimization

1. **Review Top 3-5 Results**
   - Check if they're similar or different
   - Look for consistent patterns

2. **Test Best Configuration**
   ```bash
   # Manually test the best configuration
   # Edit config/config.yaml with best parameters
   python quick_backtest.py
   ```

3. **Backtest on Different Periods**
   - Test on 3 months, 6 months, 1 year
   - See if results are consistent

4. **Apply to Live Trading**
   - Once satisfied, update config.yaml
   - Start with dry_run: true
   - Monitor performance

## Tips

1. **Start Small**: Test with 10-20 combinations first
2. **Use Multiple Periods**: Test on different time periods
3. **Balance Metrics**: Don't just optimize Sharpe or Return alone
4. **Avoid Overtrading**: If trades > 50, increase hysteresis or threshold
5. **Check Win Rate**: Should be > 50% for good strategy

## Example Workflow

```bash
# Step 1: Quick optimization (20 tests)
python optimize_backtest.py --max-tests 20

# Step 2: Review results
cat optimization_results.csv

# Step 3: Refine and test again with best ranges
# Edit optimize_backtest.py with narrower ranges around best result

# Step 4: Full optimization
python optimize_backtest.py --max-tests 50 --months 3

# Step 5: Apply best configuration
# Copy best parameters to config/config.yaml
```

## Output Files

- **optimization_results.csv**: All test results
- **config/temp_optimize_*.yaml**: Temporary config files (can delete)

## Next Steps

After finding optimal parameters:
1. Update `config/config.yaml` with best settings
2. Run full backtest: `python quick_backtest.py`
3. Review charts and metrics
4. Test in dry-run mode before going live

Happy optimizing! 🚀

