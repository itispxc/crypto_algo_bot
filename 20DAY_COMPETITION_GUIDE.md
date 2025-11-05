# 20-Day Competition Optimization Guide

## 🎯 Competition Details
- **Period**: November 10-30, 2024 (20 days)
- **Goal**: Maximum Sharpe ratio AND profit in 20 days
- **Focus**: Find optimal trade count for 20-day performance

## 🚀 Quick Start

### Step 1: Quick Optimization (10-15 minutes)
```bash
python QUICK_20DAY_OPTIMIZE.py
```

This tests:
- 54 parameter combinations
- Each on 3 random 20-day periods
- Finds optimal trade count

### Step 2: Full Optimization (30-45 minutes)
```bash
python optimize_20day.py --pairs BTC/USD ETH/USD SOL/USD BNB/USD --periods 5
```

This tests:
- 30 parameter combinations
- Each on 5 random 20-day periods
- More thorough analysis

## 📊 What Gets Tested

### Parameters Tested:
1. **Score Threshold** (0.01, 0.02, 0.03)
   - Affects signal quality
   - Lower = More trades
   - Higher = Fewer but better trades

2. **Top K Positions** (4, 6, 8)
   - Number of assets to hold
   - More = Diversification
   - Fewer = Concentration

3. **Cash Buffer** (5%, 10%, 15%)
   - Reserve cash
   - Lower = More capital deployed

4. **Hysteresis** (0.02, 0.03, 0.05, 0.10)
   - Rebalancing frequency
   - Lower = More frequent
   - Higher = Less frequent

### What's Measured:
- **Average Sharpe** across random 20-day periods
- **Average Return** across periods
- **Average Trade Count** per 20 days
- **Consistency** (lower std = more consistent)
- **Composite Score** (Sharpe + Return + Consistency)

## 🎯 Expected Results

### Optimal Trade Count for 20 Days:
- **Too Few** (< 5 trades): Missing opportunities
- **Too Many** (> 30 trades): Overtrading, fees eat profits
- **Sweet Spot**: Usually 8-20 trades per 20 days

### Good Performance:
- ✅ Sharpe > 1.5
- ✅ Return > 5% (in 20 days)
- ✅ 8-20 trades
- ✅ Win rate > 50%
- ✅ Consistent across periods

## 📈 Optimization Workflow

### Day 1: Quick Test
```bash
python QUICK_20DAY_OPTIMIZE.py
```

**Review results:**
- What's the optimal trade count?
- Which parameters give best Sharpe?
- Is performance consistent?

### Day 2: Refine
```bash
# If results look good, run full optimization
python optimize_20day.py --periods 5

# Or test specific parameter ranges
# Edit optimize_20day.py with narrower ranges
```

### Day 3: Validate
```bash
# Test best config on specific 20-day period
python backtest_advanced.py \
  --start 2024-10-15 \
  --end 2024-11-04 \
  --pairs BTC/USD ETH/USD SOL/USD
```

### Day 4: Final Test
```bash
# Test on competition dates (Nov 10-30)
python backtest_advanced.py \
  --start 2024-11-10 \
  --end 2024-11-30 \
  --pairs BTC/USD ETH/USD SOL/USD
```

## 🔍 Understanding Results

### Trade Count Analysis
The script shows performance by trade count range:
- **0-5 trades**: May miss opportunities
- **5-10 trades**: Conservative
- **10-15 trades**: Balanced (often optimal)
- **15-20 trades**: Active
- **20-30 trades**: Very active
- **30+ trades**: Overtrading risk

### Composite Score
- **60% Sharpe Ratio**: Risk-adjusted return
- **30% Return**: Absolute profit
- **10% Consistency**: Lower variance preferred

## 📝 After Optimization

### 1. Update Config
Edit `config/config.yaml` with best parameters:
```yaml
signals:
  score_threshold: [best_value]
  top_k_normal: [best_value]
  hysteresis_weight_change: [best_value]

sizing:
  cash_buffer_normal: [best_value]
```

### 2. Test Competition Period
```bash
# Test on actual competition dates
python backtest_advanced.py \
  --start 2024-11-10 \
  --end 2024-11-30
```

### 3. Monitor Performance
- Check Sharpe ratio
- Monitor trade count
- Ensure not overtrading

## 🎓 Key Insights for 20-Day Competition

### Timeframe Considerations:
- **20 days is short**: Need to be selective
- **Fees matter more**: Each trade costs 0.2% round trip
- **Consistency important**: Can't afford bad days

### Optimization Strategy:
1. **Focus on quality**: Higher score threshold
2. **Limit trades**: 8-15 trades optimal
3. **Keep cash buffer**: 10-15% for safety
4. **Higher hysteresis**: 0.05-0.10 to avoid overtrading

### Expected Optimal Configuration:
- **Score Threshold**: 0.02-0.03 (quality signals)
- **Top K**: 4-6 positions (concentration)
- **Cash Buffer**: 10-15% (safety)
- **Hysteresis**: 0.05-0.10 (less frequent)
- **Target Trades**: 8-15 per 20 days

## 📊 Results Interpretation

### Best Configuration Shows:
```
Rank 1:
  Parameters:
    Score Threshold: 0.02
    Top K (Normal): 6
    Cash Buffer: 0.10
    Hysteresis: 0.05
  Performance:
    Avg Sharpe: 2.145
    Avg Return: 8.23%
    Avg Trades: 12.3
    Consistency: 0.923
```

**This means:**
- Over multiple 20-day periods, this config averages:
  - 12.3 trades per 20 days
  - 8.23% return
  - Sharpe of 2.145
  - Consistent performance

## 🚀 Ready to Optimize?

```bash
# Quick test (10-15 min)
python QUICK_20DAY_OPTIMIZE.py

# Full optimization (30-45 min)
python optimize_20day.py --periods 5
```

The script will:
1. ✅ Test on random 20-day periods
2. ✅ Find optimal trade count
3. ✅ Show best parameters
4. ✅ Analyze by trade count range
5. ✅ Give you the best config for competition!

Good luck! 🎯

