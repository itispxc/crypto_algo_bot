"""
Main scheduler loop for the trading bot.
"""
import time
import logging
from datetime import datetime, timezone
from typing import Dict

import sys
import os
# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.data_client import DataClient
from src.state import load_state, save_state, track_peak_equity
from src.feature_engine import compute_features, compute_atr_30m
from src.regime import compute_market_regime
from src.alpha_model import load_models, score_signals
from src.portfolio import build_target_weights, scale_weights, mark_to_market
from src.execution import rebalance_to_weights, apply_stops_and_tps
from src.risk import check_drawdown_and_scale, update_stops

logger = logging.getLogger(__name__)


def run_bot(config: dict):
    """
    Main bot loop.
    
    Args:
        config: Configuration dictionary
    """
    logging.basicConfig(
        level=getattr(logging, config["ops"]["log_level"]),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("=" * 60)
    logger.info("Starting ML Trading Bot")
    logger.info("=" * 60)
    
    # Get all pairs
    pairs = (config["universe"]["tier1"] + 
             config["universe"]["tier2"] + 
             config["universe"]["tier3"])
    
    # Initialize components
    data_client = DataClient(config)
    state = load_state()
    
    # If state is empty, load from exchange
    if state.equity == 0:
        logger.info("Loading initial state from exchange...")
        state = data_client.get_positions()
        save_state(state)
    
    # Load models
    models = load_models(config)
    if not any(models.values()):
        logger.warning("No models loaded - using dummy signals")
        models = {"6h": None, "24h": None}
    
    logger.info(f"Initial equity: ${state.equity:,.2f}")
    logger.info(f"Trading {len(pairs)} pairs")
    logger.info(f"Dry run: {config['ops']['dry_run']}")
    
    last_minute = -1
    last_rebalance_check = None
    
    while True:
        try:
            now = datetime.now(timezone.utc)
            current_minute = now.minute
            current_time_str = now.strftime("%H:%M")
            
            # Intraday checks (every 15 minutes)
            if current_minute % config["scheduling"]["intraday_check_minutes"] == 0 and current_minute != last_minute:
                logger.info(f"Intraday check at {current_time_str} UTC")
                
                # Get snapshots and mark to market
                snapshots = data_client.get_all_snapshots(pairs)
                state = mark_to_market(state, snapshots)
                track_peak_equity(state)
                save_state(state)
                
                # Check drawdown
                exposure_scalar = check_drawdown_and_scale(state, config)
                
                # Update stops
                # Get 30m candles for ATR
                candles_30m = {}
                for pair in pairs[:5]:  # Limit to avoid rate limits
                    candles_30m[pair] = data_client.get_candles(pair, "30m", 50)
                    time.sleep(config["exchange"]["rate_limit_ms"] / 1000.0)
                
                atrs = compute_atr_30m(list(candles_30m.keys()), candles_30m)
                state = update_stops(state, atrs, snapshots, None, config)
                
                # Apply stops
                apply_stops_and_tps(state, snapshots, data_client, config)
                
                logger.info(f"Equity: ${state.equity:,.2f} | Peak: ${state.peak_equity:,.2f} | DD: {(state.equity - state.peak_equity) / max(state.peak_equity, 1):.2%}")
                
                last_minute = current_minute
            
            # Feature update and scoring (every 30 minutes)
            if current_minute in (0, 30) and current_minute != last_minute:
                logger.info(f"Feature update at {current_time_str} UTC")
                
                try:
                    # Fetch candles
                    logger.info("Fetching candles...")
                    candles_5m = {}
                    candles_30m = {}
                    
                    for pair in pairs:
                        candles_5m[pair] = data_client.get_candles(pair, "5m", 600)
                        candles_30m[pair] = data_client.get_candles(pair, "30m", 600)
                        time.sleep(config["exchange"]["rate_limit_ms"] / 1000.0)
                    
                    # Compute features
                    logger.info("Computing features...")
                    features = compute_features(candles_5m, candles_30m, config)
                    
                    # Compute regime
                    btc_candles = candles_30m.get("BTC/USD", [])
                    if btc_candles:
                        regime_info = compute_market_regime(btc_candles)
                        logger.info(f"Market regime: {regime_info['regime']} ({regime_info['vol_regime']} vol)")
                    else:
                        regime_info = {"regime": "chop", "vol_regime": "mid", "breadth": 0.5}
                    
                    # Score signals
                    logger.info("Scoring signals...")
                    signals = score_signals(models, features, regime_info, config)
                    
                    # Build target weights
                    logger.info("Building target weights...")
                    target_w = build_target_weights(signals, regime_info, state, config)
                    
                    # Scale by exposure
                    exposure_scalar = check_drawdown_and_scale(state, config)
                    target_w = scale_weights(target_w, exposure_scalar)
                    
                    # Get snapshots
                    snapshots = data_client.get_all_snapshots(pairs)
                    state = mark_to_market(state, snapshots)
                    
                    # Rebalance
                    logger.info("Rebalancing...")
                    orders = rebalance_to_weights(target_w, state, snapshots, data_client, config)
                    
                    if orders:
                        logger.info(f"Placed {len(orders)} orders")
                    
                    save_state(state)
                    
                except Exception as e:
                    logger.error(f"Error in feature update: {e}", exc_info=True)
                
                last_minute = current_minute
            
            # Full rebalance at scheduled times
            if current_time_str in config["scheduling"]["rebalance_times_utc"] and current_time_str != last_rebalance_check:
                logger.info(f"Full rebalance at {current_time_str} UTC")
                
                try:
                    # Force time-stop exits if needed
                    # (Implementation depends on requirements)
                    
                    # Re-run feature update logic with lower hysteresis
                    # ... (similar to above)
                    
                    last_rebalance_check = current_time_str
                except Exception as e:
                    logger.error(f"Error in full rebalance: {e}", exc_info=True)
            
            # Sleep
            sleep_time = max(1, config["exchange"]["rate_limit_ms"] // 1000)
            time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            save_state(state)
            break
        except Exception as e:
            logger.exception(f"Error in main loop: {e}")
            time.sleep(60)

