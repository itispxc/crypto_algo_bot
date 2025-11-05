# TradingView-Style Backtesting System

## ✅ What You Have Now

I've created a comprehensive backtesting system similar to TradingView with:

### 📊 Visualizations

1. **Equity Curve Chart**
   - Shows portfolio value over time
   - Green area = Profit
   - Red area = Loss
   - Compares to initial balance

2. **Price Chart with Trades**
   - Price movement line
   - Green triangles = Buy signals
   - Red triangles = Sell signals
   - Shows exact entry/exit points

3. **Drawdown Chart**
   - Visual representation of risk
   - Shows recovery periods
   - Percentage drawdown over time

4. **Returns Distribution**
   - Histogram of returns
   - Shows if strategy is consistently profitable

5. **Trade P&L Bars**
   - Green bars = Winning trades
   - Red bars = Losing trades
   - Individual trade performance

6. **Performance Metrics Table**
   - All key metrics in one place

### 📈 Performance Metrics

- **Sharpe Ratio** - Risk-adjusted return
- **Sortino Ratio** - Downside-adjusted return  
- **Calmar Ratio** - Return vs max drawdown
- **Max Drawdown** - Worst peak-to-trough decline
- **Win Rate** - Percentage of profitable trades
- **Total Return** - Absolute and percentage
- **Average Profit/Trade** - Average trade performance

## 🚀 How to Use

### Quick Test (1 Month)

```bash
python quick_backtest.py
```

### Interactive Backtest

```bash
python run_backtest.py
```

Follow the prompts:
1. Select time period (1 month, 3 months, 1 year, custom)
2. Choose trading pairs
3. View results

### Command Line

```bash
# Last month
python backtest_advanced.py --months 1

# Last year
python backtest_advanced.py --years 1

# Specific dates
python backtest_advanced.py --start 2024-01-01 --end 2024-12-31

# Custom pairs
python backtest_advanced.py --months 3 --pairs BTC/USD ETH/USD SOL/USD
```

## 📅 Time Periods Supported

- **1 month** - Quick test
- **3 months** - Quarter analysis
- **6 months** - Half year
- **1 year** - Full year
- **Custom** - Any date range you specify

## 📊 What Gets Generated

1. **`backtest_results.png`** - Full visualization with all charts
2. **Console output** - Performance metrics summary
3. **Trade history** - List of all trades with P&L

## 🎯 Example Output

When you run a backtest, you'll see:

```
============================================================
BACKTEST RESULTS
============================================================
Initial Balance:     $50,000.00
Final Balance:       $59,401.54
Total Return:        $9,401.54 (18.80%)

Risk Metrics:
  Sharpe Ratio:      1.234
  Sortino Ratio:     1.567
  Calmar Ratio:      0.925
  Max Drawdown:      -12.34%

Trading Stats:
  Total Trades:      42
  Win Rate:          52.38%
  Avg Profit/Trade:  $223.85
============================================================
```

Plus a comprehensive chart saved to `backtest_results.png`.

## 🔧 Customization

### Adjust Strategy Parameters

Edit `config/config.yaml`:
- `signals.score_threshold` - Minimum signal quality
- `sizing.cash_buffer_*` - Cash reserves by regime
- `stops.atr_init` - Stop loss distance
- `risk.soft_dd` / `hard_dd` - Drawdown limits

### Test Different Configurations

```bash
# Test conservative
python backtest_advanced.py --months 3 --config config/config_conservative.yaml

# Test aggressive
python backtest_advanced.py --months 3 --config config/config_aggressive.yaml
```

## 📊 Interpreting Results

### Good Strategy
- ✅ Sharpe Ratio > 1.5
- ✅ Positive total return
- ✅ Win rate > 50%
- ✅ Max drawdown < 15%
- ✅ Consistent equity curve growth

### Needs Improvement
- ⚠️ Sharpe Ratio < 1.0
- ⚠️ Negative returns
- ⚠️ Win rate < 40%
- ⚠️ Max drawdown > 25%
- ⚠️ Erratic equity curve

## 💡 Tips

1. **Start with 1 month** to test quickly
2. **Use top 5 pairs** for faster backtests
3. **Compare configurations** to find optimal settings
4. **Focus on Sharpe ratio** - best single metric
5. **Review trade history** to understand strategy behavior

## 📁 Files Created

- `backtest_advanced.py` - Main backtesting engine
- `run_backtest.py` - Interactive interface
- `quick_backtest.py` - Quick one-liner
- `BACKTEST_GUIDE.md` - Detailed guide
- `backtest_results.png` - Generated charts (after running)

## 🎨 Chart Features

The generated charts include:
- Professional styling
- Color-coded profit/loss
- Trade markers on price charts
- Multiple timeframes
- Export-ready (300 DPI)

## Next Steps

1. **Run your first backtest**:
   ```bash
   python quick_backtest.py
   ```

2. **Review the charts** in `backtest_results.png`

3. **Analyze the metrics** - Is Sharpe ratio good? Win rate acceptable?

4. **Adjust parameters** in `config/config.yaml` if needed

5. **Re-run** to compare results

6. **When satisfied**, test with real API (dry-run mode)

## Real Historical Data

Currently uses synthetic data for demonstration. To use real data:

1. **Download historical data** (CSV format)
2. **Place in a `data/` folder**
3. **Modify `load_historical_data()`** to read from files
4. **Or integrate Horus API** if available

The structure is ready - just plug in your data source!

---

**You now have a complete TradingView-style backtesting system!** 🎉

Run `python quick_backtest.py` to see it in action!

