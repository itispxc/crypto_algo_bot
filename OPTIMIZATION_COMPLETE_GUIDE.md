# Complete Optimization Guide - Multi-Timeframe & Strategy Tuning

## 🎯 Goal
Find optimal parameters that give **best Sharpe ratio AND profit** across multiple timeframes.

## 📊 Optimization Strategy

### Step 1: Test Across Timeframes (Critical!)

**Why?** A strategy that works for 1 month but fails at 3 months is not robust.

```bash
# Test your current strategy on multiple periods
python optimize_comprehensive.py --pairs BTC/USD ETH/USD SOL/USD
```

This tests:
- ✅ 1 Month
- ✅ 3 Months  
- ✅ 6 Months
- ✅ 1 Year

**Look for:**
- Consistent Sharpe across timeframes (std < 1.0)
- Positive returns in all periods
- Reasonable trade counts

### Step 2: Optimize Rebalancing Frequency

**Current:** Every 30 minutes (or at scheduled times)

**Question:** Is 30 minutes optimal?

**Test via hysteresis:**
- Lower hysteresis (0.01-0.02) = More frequent rebalancing
- Higher hysteresis (0.05-0.10) = Less frequent rebalancing

```bash
# This is included in comprehensive optimization
python optimize_comprehensive.py
```

**What to look for:**
- Sweet spot where more trades ≠ better Sharpe
- Optimal trade count (usually 8-20 per month)
- Fee efficiency (return per trade)

### Step 3: Parameter Grid Search

**Key parameters to optimize:**

1. **Score Threshold** (0.01, 0.02, 0.03)
   - Lower = More trades
   - Higher = Fewer but better trades

2. **Top K Positions** (4, 6, 8, 10)
   - More positions = Diversification
   - Fewer positions = Concentration

3. **Cash Buffer** (5%, 10%, 15%, 20%)
   - Lower = More capital deployed
   - Higher = More safety

4. **Hysteresis** (0.02, 0.03, 0.05)
   - Lower = More rebalancing
   - Higher = Less rebalancing

## 🚀 Quick Start Optimization

### Option 1: Quick Test (5-10 minutes)
```bash
python optimize_comprehensive.py --quick --pairs BTC/USD ETH/USD
```

### Option 2: Full Optimization (30-60 minutes)
```bash
python optimize_comprehensive.py --pairs BTC/USD ETH/USD SOL/USD BNB/USD
```

## 📈 Step-by-Step Optimization Process

### Phase 1: Baseline (Current Settings)
```bash
# Test current config across timeframes
python optimize_comprehensive.py --quick
```

**Record baseline:**
- Sharpe: ?
- Return: ?
- Trades: ?

### Phase 2: Timeframe Consistency
```bash
# Review timeframe_results.csv
# Look for consistent Sharpe across all periods
```

**If inconsistent:**
- Strategy may be overfitted to specific market conditions
- Consider more conservative parameters
- Increase cash buffer for stability

### Phase 3: Frequency Optimization
```bash
# Review frequency_results.csv
# Find optimal trade count
```

**Optimal trade count:**
- Too few (< 5): Missing opportunities
- Too many (> 50): Overtrading, fees eating profits
- **Sweet spot: 8-20 trades per month**

### Phase 4: Parameter Tuning
```bash
# Review parameters_results.csv
# Find best configuration
```

**Update config.yaml with best parameters:**
```yaml
signals:
  score_threshold: [best_value]  # e.g., 0.02
  top_k_normal: [best_value]     # e.g., 6
  hysteresis_weight_change: [best_value]  # e.g., 0.03

sizing:
  cash_buffer_normal: [best_value]  # e.g., 0.10
```

### Phase 5: Validation
```bash
# Test best config on longer period
python backtest_advanced.py --pairs BTC/USD ETH/USD --years 1
```

## 🔍 Understanding Results

### Good Strategy
- ✅ Sharpe > 1.5 across all timeframes
- ✅ Sharpe consistency (std < 1.0)
- ✅ Positive returns in all periods
- ✅ 8-20 trades per month
- ✅ Win rate > 50%

### Needs Improvement
- ⚠️ Sharpe varies widely across timeframes
- ⚠️ Negative returns in some periods
- ⚠️ Too many trades (> 50/month)
- ⚠️ Win rate < 40%

## 📊 Example Optimization Workflow

### Week 1: Baseline + Quick Tests
```bash
# Day 1: Baseline
python optimize_comprehensive.py --quick

# Day 2-3: Test different parameter ranges
python optimize_backtest.py --max-tests 30

# Day 4-5: Analyze results
# Review CSV files, identify patterns
```

### Week 2: Refinement
```bash
# Narrow parameter ranges around best results
# Edit optimize_comprehensive.py with refined ranges

# Test on longer periods
python backtest_advanced.py --months 3
python backtest_advanced.py --months 6
```

### Week 3: Validation
```bash
# Test on full year
python backtest_advanced.py --years 1

# Compare results across different market conditions
# If consistent, ready for live trading!
```

## 🎯 Optimization Targets

### For High Sharpe
- **Score threshold**: Higher (0.03-0.05)
- **Hysteresis**: Higher (0.05-0.10)
- **Cash buffer**: Higher (15-20%)
- **Result**: Fewer but better trades, lower risk

### For High Profit
- **Score threshold**: Lower (0.01-0.02)
- **Top K**: Higher (8-10 positions)
- **Cash buffer**: Lower (5-10%)
- **Result**: More positions, more active trading

### For Balance (Recommended)
- **Score threshold**: 0.02
- **Top K**: 6-8
- **Cash buffer**: 10%
- **Hysteresis**: 0.03
- **Result**: Good Sharpe + decent returns

## 📝 Optimization Checklist

- [ ] Test baseline across 1M, 3M, 6M, 1Y
- [ ] Check Sharpe consistency
- [ ] Optimize rebalancing frequency
- [ ] Find optimal trade count
- [ ] Test parameter combinations
- [ ] Validate on longer periods
- [ ] Check fee impact
- [ ] Verify win rate > 50%
- [ ] Update config.yaml with best settings
- [ ] Final validation backtest

## 🔧 Advanced: Custom Optimization

Edit `optimize_comprehensive.py` to test your own ranges:

```python
# In _optimize_parameters method
param_ranges = {
    'score_threshold': [0.015, 0.02, 0.025],  # Narrow range around best
    'top_k_normal': [5, 6, 7],  # Test around optimal
    'cash_buffer_normal': [0.08, 0.10, 0.12],
    'hysteresis': [0.025, 0.03, 0.035],
}
```

## 📊 Interpreting Results

### Timeframe Results
- **Consistent Sharpe**: Strategy is robust
- **Varying Sharpe**: May need different params per regime

### Frequency Results
- **Optimal trades**: Usually 8-20/month
- **Diminishing returns**: More trades ≠ better Sharpe

### Parameter Results
- **Top configuration**: Highest composite score
- **Check consistency**: Does it work across timeframes?

## 🎓 Best Practices

1. **Start broad, then narrow**
   - Test wide ranges first
   - Narrow around best results

2. **Test multiple timeframes**
   - Don't optimize for 1 month only
   - Ensure consistency

3. **Balance metrics**
   - Don't optimize only Sharpe
   - Don't optimize only return
   - Use composite score

4. **Consider fees**
   - More trades = More fees
   - Find optimal trade count

5. **Validate thoroughly**
   - Test on unseen periods
   - Check robustness

## 🚦 When to Stop Optimizing

**Stop when:**
- ✅ Sharpe > 1.5 across all timeframes
- ✅ Consistent performance
- ✅ Reasonable trade count (8-20/month)
- ✅ Win rate > 50%
- ✅ Results validated on multiple periods

**Don't over-optimize:**
- Too many tests = Overfitting
- Test on validation period
- If results degrade, revert

## 📈 Next Steps After Optimization

1. **Update config.yaml** with best parameters
2. **Run final validation** on 1 year
3. **Review charts** - do they look good?
4. **Test in dry-run** mode before live
5. **Monitor live performance** and adjust

---

**Ready to optimize?** Run:
```bash
python optimize_comprehensive.py --quick
```

This will test your strategy across timeframes and parameters to find the best configuration! 🚀

