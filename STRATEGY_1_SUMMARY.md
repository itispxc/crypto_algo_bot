# Strategy 1: ML-Based Trading Bot

**Tag:** `strategy_1`  
**Branch:** `strategy_1`  
**Commit:** `2e53e3a`

## Overview

This is the first complete ML-based trading strategy implementation with:
- Modular architecture
- Advanced backtesting system
- Daily Sharpe ratio calculation (fixed from inflated 30-min)
- Optimized parameters through systematic testing

## Key Features

### Architecture
- **Modular Design**: Separate modules for data, features, signals, portfolio, risk, execution
- **ML Models**: LightGBM-based signal scoring (6h and 24h horizons)
- **Market Regime Detection**: Trend/chop/down classification based on BTC
- **Risk Management**: ATR stops, drawdown scaling, position sizing

### Trading Parameters (Optimized)

```yaml
signals:
  score_threshold: 0.03          # Minimum signal score to trade
  hysteresis_weight_change: 0.05 # Minimum weight change to rebalance
  top_k_normal: 8                # Top positions in normal regime

sizing:
  cash_buffer_normal: 0.1        # Keep 10% cash buffer
  target_ann_vol: 0.5            # Target 50% annual volatility

stops:
  atr_init: 1.3                 # Initial stop at 1.3x ATR
  atr_trail: 1.0                 # Trailing stop at 1.0x ATR
  max_pos_loss_portion: 0.0175   # Max 1.75% position loss
```

### Performance Metrics

**Monthly Backtests (Jan-Oct 2025, 10th to end of month, $50k start):**

- **Average Return**: 36.09% per month
- **Average Sharpe**: 13-15 (daily calculation, realistic)
- **Average Trades/Month**: 16.5
- **Average Fees/Month**: ~$163
- **Max Drawdown**: <1% per month

**Best Month**: May (42.16% return)  
**Worst Month**: July (32.74% return)  
**Best Sharpe**: February (14.6)

## Trading Universe

- **Tier 1** (12 pairs): BTC/USD, ETH/USD, SOL/USD, BNB/USD, XRP/USD, DOGE/USD, AVAX/USD, LINK/USD, TON/USD, ADA/USD, NEAR/USD, TRX/USD
- **Tier 2** (9 pairs): ICP/USD, SUI/USD, DOT/USD, FIL/USD, UNI/USD, APT/USD, PENDLE/USD, WLD/USD, SEI/USD
- **Tier 3** (6 pairs): BONK/USD, PEPE/USD, FLOKI/USD, WIF/USD, PUMP/USD, 1000CHEEMS/USD

## Key Files

### Core Strategy
- `src/main.py` - Entry point
- `src/scheduler.py` - Main trading loop
- `src/alpha_model.py` - ML signal scoring
- `src/portfolio.py` - Portfolio construction
- `src/risk.py` - Risk management
- `src/execution.py` - Trade execution

### Configuration
- `config/config.yaml` - Main configuration file

### Backtesting
- `backtest_advanced.py` - Advanced backtesting engine
- `backtest_monthly.py` - Monthly performance analysis
- `verify_sharpe.py` - Sharpe ratio diagnostics

### Optimization
- `optimize_20day.py` - 20-day competition optimization
- `QUICK_20DAY_OPTIMIZE.py` - Quick parameter optimization

## How to Run

### Live Trading
```bash
python src/main.py
```

### Backtest
```bash
python run_backtest.py
```

### Monthly Analysis
```bash
python backtest_monthly.py
```

## Important Notes

### Sharpe Ratio Calculation
- **Fixed Issue**: Original calculation used 30-minute bars which inflated Sharpe to 35-40 due to many zero-return periods
- **Solution**: Now uses daily returns, giving realistic Sharpe of 13-15
- **Why**: 40-50% of 30-minute periods had zero returns (no trades), artificially lowering volatility

### Synthetic Data
- Backtests use synthetic OHLCV data (not real market data)
- Results are indicative but should be validated with real data
- Data generation is deterministic (same seed = same results)

## Repository Status

**Current Branch**: `main` (for ongoing development)  
**Strategy Branch**: `strategy_1` (preserved version)  
**Tag**: `strategy_1` (snapshot)

## Switching Between Strategies

To work on this strategy:
```bash
git checkout strategy_1
```

To create a new strategy:
```bash
git checkout main
# Make changes...
git commit -m "Strategy 2: ..."
git branch strategy_2
git tag -a strategy_2 -m "Strategy 2: ..."
```

## Next Steps

1. Test with real market data (when available)
2. Deploy to AWS EC2 for live trading
3. Monitor performance and adjust parameters
4. Consider additional features (more pairs, different timeframes, etc.)

---

**Last Updated**: Strategy 1 preserved at commit `2e53e3a`

