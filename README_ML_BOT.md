# ML Trading Bot - Advanced Implementation

This is the advanced ML-based trading bot implementation with regime detection, risk management, and portfolio optimization.

## Architecture Overview

The bot uses a sophisticated ML-based approach with:
- **LightGBM models** for signal generation (6h and 24h horizons)
- **Regime detection** (trend/chop/down) for adaptive strategy
- **Multi-asset portfolio** optimization with tiered risk caps
- **Dynamic stop losses** with ATR-based trailing stops
- **Drawdown protection** with exposure scaling

## Project Structure

```
crypto_algo_bot/
├── config/
│   └── config.yaml          # Main configuration
├── src/
│   ├── main.py               # Entry point
│   ├── scheduler.py          # Main loop
│   ├── data_client.py        # Data fetching & execution
│   ├── feature_engine.py     # Feature computation
│   ├── regime.py             # Market regime detection
│   ├── alpha_model.py        # ML signal scoring
│   ├── portfolio.py          # Portfolio construction
│   ├── risk.py               # Risk management
│   ├── execution.py          # Order execution
│   ├── state.py              # State persistence
│   ├── metrics.py            # Performance metrics
│   ├── utils.py              # Utilities
│   └── data_classes.py       # Data structures
├── models/
│   ├── lgbm_6h.txt          # 6h horizon model (add your trained model)
│   └── lgbm_24h.txt         # 24h horizon model (add your trained model)
├── logs/                     # Log files
└── state.json                # Portfolio state persistence
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure

Edit `config/config.yaml`:
- Set `dry_run: true` for testing (won't place real orders)
- Adjust trading pairs, risk parameters, etc.

### 3. Add Models (Optional)

Place trained LightGBM models in `models/`:
- `lgbm_6h.txt` - 6-hour prediction model
- `lgbm_24h.txt` - 24-hour prediction model

If models are missing, the bot will use a simple fallback scoring method.

### 4. Run Bot

```bash
cd src
python main.py
```

## Configuration

### Trading Universe

The bot trades three tiers of assets:
- **Tier 1**: Major coins (BTC, ETH, SOL, etc.) - 15% max position
- **Tier 2**: Mid-cap coins - 10% max position
- **Tier 3**: Meme/small-cap coins - 5% max position, 12% total sleeve

### Regime-Based Strategy

The bot adapts to market conditions:
- **Trend**: Holds 8 positions, 10% cash buffer
- **Chop**: Holds 6 positions, 20% cash buffer
- **Down**: Holds 4 positions, 60% cash buffer

### Risk Management

- **ATR-based stops**: Initial stop at entry - 1.3*ATR
- **Trailing stops**: Activated after 0.8*ATR profit move
- **Max position loss**: 1.75% stop loss per position
- **Drawdown scaling**: 
  - Soft DD (5%): Scale to 50% exposure
  - Hard DD (10%): Scale to 20% exposure

## Key Features

### 1. Feature Engineering

Computes 13 features per asset:
- Momentum: 1h, 3h, 6h, 24h returns
- Mean reversion: EMA z-scores, RSI, Bollinger position
- Volatility: Realized vol, ATR, drawdown from peak
- Tier classification

### 2. ML Signal Scoring

- Ensemble of 6h and 24h models
- Regime-weighted predictions
- Cost-adjusted expected returns (fees + slippage)

### 3. Portfolio Construction

- Inverse-volatility sizing
- Score-tilted weights
- Tier-based position caps
- Cash buffer by regime
- Hysteresis to reduce turnover

### 4. Execution

- Limit orders near mid-price
- Hysteresis prevents micro-adjustments
- Minimum order size enforcement
- Precision rounding for exchange requirements

## Model Training (Future Work)

To train your own models:

1. **Collect data**: Historical 5m/30m bars for last 180 days
2. **Build features**: Use `feature_engine.py` logic
3. **Create targets**: Forward 6h/24h vol-normalized returns
4. **Train LightGBM**: Use purged time-series CV
5. **Save models**: Export to `models/lgbm_6h.txt` and `models/lgbm_24h.txt`

## Current Status

✅ **Implemented:**
- Full architecture and modules
- Roostoo API integration
- Feature engineering
- Regime detection
- Portfolio construction
- Risk management
- State persistence

⚠️ **Needs Models:**
- LightGBM models for 6h/24h horizons
- Without models, bot uses simple fallback scoring

## Running Without Models

The bot will work without trained models, but will use a simplified scoring method. For best performance, train and add models.

## Monitoring

- Check logs in console
- Portfolio state saved to `state.json`
- Metrics computed in real-time

## Next Steps

1. **Train models** using historical data
2. **Backtest** the strategy
3. **Test in dry-run mode** (`dry_run: true`)
4. **Deploy to AWS** when ready

## Differences from Simple Bot

This ML bot includes:
- Multi-asset portfolio (vs single pair)
- Regime-adaptive strategy
- ML-based signal generation
- Sophisticated risk management
- Dynamic position sizing
- Trailing stop losses

The simple moving average bot (`main.py` in root) is still available for basic strategies.

