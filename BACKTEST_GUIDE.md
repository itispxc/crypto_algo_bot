# Backtesting Guide - TradingView Style

## Overview

The advanced backtesting system provides TradingView-style visualization with:
- **Equity curve** showing profit over time
- **Performance metrics** (Sharpe, Sortino, Calmar ratios)
- **Price charts** with buy/sell markers
- **Drawdown visualization**
- **Trade P&L analysis**
- **Historical data support** (months to years)

## Quick Start

### Option 1: Interactive Backtest

```bash
python run_backtest.py
```

This will guide you through:
1. Selecting time period (1 month, 3 months, 1 year, etc.)
2. Choosing trading pairs
3. Running the backtest
4. Viewing results

### Option 2: Command Line

```bash
# Backtest last month with top 5 pairs
python backtest_advanced.py --months 1

# Backtest specific date range
python backtest_advanced.py --start 2024-01-01 --end 2024-12-31

# Backtest last year with all Tier 1 pairs
python backtest_advanced.py --years 1 --pairs BTC/USD ETH/USD SOL/USD BNB/USD

# Custom configuration
python backtest_advanced.py --months 6 --pairs BTC/USD ETH/USD --config config/config.yaml
```

### Option 3: Python Script

```python
from backtest_advanced import run_backtest_advanced

# Backtest last 3 months
results = run_backtest_advanced(
    pairs=['BTC/USD', 'ETH/USD', 'SOL/USD'],
    months=3
)

# Backtest specific date range
results = run_backtest_advanced(
    pairs=['BTC/USD', 'ETH/USD'],
    start_date='2024-01-01',
    end_date='2024-12-31'
)
```

## What the Charts Show

### 1. Equity Curve (Top)
- Green area = Profit above initial balance
- Red area = Loss below initial balance
- Shows portfolio value over time

### 2. Price Chart with Trades
- Blue line = Price movement
- Green triangles = Buy signals
- Red triangles = Sell signals
- Shows where trades were executed

### 3. Drawdown Chart
- Red area = Drawdown percentage
- Shows risk and recovery periods

### 4. Returns Distribution
- Histogram of returns
- Shows profitability distribution

### 5. Trade P&L
- Green bars = Profitable trades
- Red bars = Losing trades
- Shows individual trade performance

### 6. Performance Metrics Table
- Total return (absolute and %)
- Risk-adjusted metrics (Sharpe, Sortino, Calmar)
- Trading statistics (win rate, avg profit)

## Performance Metrics Explained

### Sharpe Ratio
- **Good**: > 1.0
- **Excellent**: > 2.0
- Measures risk-adjusted return

### Sortino Ratio
- Similar to Sharpe but only penalizes downside volatility
- **Good**: > 1.5
- Better for asymmetric strategies

### Calmar Ratio
- Annual return / Max drawdown
- **Good**: > 1.0
- Measures return relative to worst drawdown

### Max Drawdown
- Largest peak-to-trough decline
- **Acceptable**: < 20%
- **Risky**: > 30%

## Using Real Historical Data

### Option 1: CSV Files

Create CSV files with format:
```csv
timestamp,open,high,low,close,volume
2024-01-01 00:00:00,50000,50100,49900,50050,1000
2024-01-01 00:05:00,50050,50150,50000,50100,1200
...
```

Then modify `backtest_advanced.py` to load:
```python
df = backtester.load_data_from_csv('data/BTC_USD_5m.csv')
```

### Option 2: Horus Data Source

If you have access to Horus, integrate their API:
```python
def load_from_horus(pair, start, end):
    # Implement Horus API integration
    # Return DataFrame with OHLCV data
    pass
```

### Option 3: Exchange Historical Data

Some exchanges provide historical data APIs. You can:
1. Download historical data
2. Convert to CSV format
3. Load using `load_data_from_csv()`

## Backtest Examples

### Example 1: Quick 1-Month Test
```bash
python run_backtest.py
# Select: a (1 month), a (top 5 pairs)
```

### Example 2: Full Year Analysis
```bash
python backtest_advanced.py --years 1 --pairs BTC/USD ETH/USD SOL/USD
```

### Example 3: Specific Period
```bash
python backtest_advanced.py --start 2024-06-01 --end 2024-12-31
```

## Interpreting Results

### Good Results
- ✅ Sharpe Ratio > 1.5
- ✅ Positive total return
- ✅ Win rate > 50%
- ✅ Max drawdown < 15%

### Needs Improvement
- ⚠️ Sharpe Ratio < 1.0
- ⚠️ Negative returns
- ⚠️ Win rate < 40%
- ⚠️ Max drawdown > 25%

### Adjusting Strategy

If results are poor, adjust in `config/config.yaml`:
- `signals.score_threshold` - Higher = fewer but better trades
- `sizing.cash_buffer_*` - More cash = less risk
- `stops.atr_init` - Tighter stops = more protection
- `risk.soft_dd` / `hard_dd` - Earlier drawdown protection

## Comparing Strategies

Run multiple backtests with different configs:
```bash
# Test 1: Conservative
cp config/config.yaml config/config_conservative.yaml
# Edit: higher cash_buffer, tighter stops
python backtest_advanced.py --config config/config_conservative.yaml

# Test 2: Aggressive  
cp config/config.yaml config/config_aggressive.yaml
# Edit: lower cash_buffer, wider stops
python backtest_advanced.py --config config/config_aggressive.yaml
```

Compare results to find optimal parameters.

## Advanced Usage

### Backtest Multiple Time Periods

```python
from backtest_advanced import run_backtest_advanced

periods = [
    {'months': 1, 'name': 'Last Month'},
    {'months': 3, 'name': 'Last Quarter'},
    {'months': 6, 'name': 'Last 6 Months'},
    {'years': 1, 'name': 'Last Year'}
]

for period in periods:
    print(f"\nBacktesting: {period['name']}")
    results = run_backtest_advanced(**period)
    print(f"Sharpe: {results['sharpe_ratio']:.2f}, Return: {results['total_return_pct']:.2f}%")
```

### Save Results

```python
import json

results = run_backtest_advanced(months=3)
# Save metrics
with open('backtest_results.json', 'w') as f:
    json.dump({
        'total_return_pct': results['total_return_pct'],
        'sharpe_ratio': results['sharpe_ratio'],
        'max_drawdown': results['max_drawdown_pct'],
        'win_rate': results['win_rate']
    }, f, indent=2)
```

## Tips

1. **Start with shorter periods** (1 month) to test quickly
2. **Use top 5 pairs** for faster backtests
3. **Compare multiple configs** to optimize
4. **Focus on Sharpe ratio** - it's the best single metric
5. **Check drawdown** - ensure it's acceptable
6. **Review trade history** - understand why trades were made

## Troubleshooting

### "No data loaded"
- Check date range is valid
- Ensure data files exist (if using CSV)
- Verify pair names match exchange format

### "Insufficient data"
- Increase date range
- Use fewer pairs
- Check data quality

### Charts not showing
- Ensure matplotlib is installed: `pip install matplotlib`
- Check if running in headless environment (use `plt.savefig()` instead)

## Next Steps

1. **Run initial backtest** to see current strategy performance
2. **Adjust parameters** in `config/config.yaml`
3. **Compare results** with different settings
4. **Optimize** for best Sharpe ratio
5. **Test in dry-run** before live trading

Happy backtesting! 📈

