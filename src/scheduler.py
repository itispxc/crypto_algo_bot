"""
Main scheduler loop for the trading bot.
"""
import time
import math
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


def _round_to_step(value: float, step: float, direction: str = "nearest") -> float:
    """
    Align a value to the exchange-defined step size.
    direction: 'ceil', 'floor', or 'nearest'
    """
    if not step or step <= 0:
        return value
    ratio = value / step
    if direction == "ceil":
        ratio = math.ceil(ratio - 1e-12)
    elif direction == "floor":
        ratio = math.floor(ratio + 1e-12)
    else:
        ratio = round(ratio)
    return ratio * step


def maybe_run_fast_start(state, data_client, config):
    """
    Execute the tournament fast-start routine:
    - Buy BTC with available cash
    - Wait for a 5% (configurable) gain, then exit and resume normal trading
    """
    fast_cfg = config.get("tournament_fast_start", {})
    if not fast_cfg.get("enabled", False):
        return state, False

    if state.fast_start_completed:
        return state, False

    pair = fast_cfg.get("pair", "BTC/USD")
    take_profit_pct = fast_cfg.get("take_profit_pct", 0.05)
    slippage_pct = fast_cfg.get("limit_slippage_pct", 0.002)
    min_cash_reserve = fast_cfg.get("min_cash_reserve", 0.0)
    fee_rate = config["exchange"].get("fee_bps", 0) / 10_000.0
    min_order_usd = config["exchange"].get("min_order_usd", 0.0)
    pair_filters = data_client.get_pair_filters(pair)
    price_step = pair_filters.get("price_step")
    qty_step = pair_filters.get("qty_step")
    min_qty = pair_filters.get("min_qty", 0.0)
    min_notional = pair_filters.get("min_notional", 0.0)

    snapshot = data_client.get_snapshot(pair)
    if not snapshot:
        logger.warning("Fast start: unable to get snapshot for %s", pair)
        return state, True

    current_price = snapshot.price or snapshot.ask or snapshot.bid
    if not current_price or current_price <= 0:
        logger.warning("Fast start: invalid price for %s", pair)
        return state, True

    if not state.fast_start_active:
        usable_cash = max(0.0, state.cash_usd - min_cash_reserve)
        if usable_cash < min_order_usd:
            logger.warning("Fast start: not enough cash (%.2f) to bootstrap trade", usable_cash)
            state.fast_start_completed = True
            save_state(state)
            return state, False

        limit_price = current_price * (1 + slippage_pct)
        limit_price = _round_to_step(limit_price, price_step, "ceil")
        qty = (usable_cash * (1 - fee_rate)) / limit_price
        qty = _round_to_step(qty, qty_step, "floor")
        if qty <= 0:
            logger.warning("Fast start: computed qty <= 0")
            state.fast_start_completed = True
            save_state(state)
            return state, False

        if min_qty and qty < min_qty:
            logger.warning("Fast start: qty %.8f below min qty %.8f", qty, min_qty)
            state.fast_start_completed = True
            save_state(state)
            return state, False

        if min_notional and (qty * limit_price) < min_notional:
            logger.warning("Fast start: notional %.2f below min %.2f", qty * limit_price, min_notional)
            state.fast_start_completed = True
            save_state(state)
            return state, False

        logger.info("Fast start: buying %.6f %s @ %.2f (target +%.1f%%)", qty, pair, limit_price, take_profit_pct * 100)
        order_id = data_client.place_order(pair=pair, side="buy", qty=qty, price=limit_price)
        if order_id:
            refreshed_state = data_client.get_positions()
            refreshed_state.fast_start_active = True
            refreshed_state.fast_start_completed = False
            refreshed_state.fast_start_entry_price = limit_price
            target_price = limit_price * (1 + take_profit_pct + 2 * fee_rate)
            refreshed_state.fast_start_target_price = target_price
            save_state(refreshed_state)
            return refreshed_state, True

        logger.error("Fast start: buy order failed, will retry")
        return state, True

    # Already long BTC, wait for target
    target_price = state.fast_start_target_price
    if not target_price and state.fast_start_entry_price:
        target_price = state.fast_start_entry_price * (1 + take_profit_pct + 2 * fee_rate)
        state.fast_start_target_price = target_price
        save_state(state)

    if not target_price:
        logger.warning("Fast start: missing target price, resetting state")
        state.fast_start_active = False
        save_state(state)
        return state, False

    logger.info(
        "Fast start: monitoring %s price %.2f vs target %.2f",
        pair,
        current_price,
        target_price,
    )

    if current_price >= target_price:
        position = state.positions.get(pair)
        if not position or position.quantity <= 0:
            logger.warning("Fast start: no position found to exit, marking complete")
            state.fast_start_active = False
            state.fast_start_completed = True
            save_state(state)
            return state, False

        exit_price = current_price * (1 - slippage_pct)
        exit_price = _round_to_step(exit_price, price_step, "floor")
        sell_qty = _round_to_step(position.quantity, qty_step, "floor") if position else 0.0
        if sell_qty <= 0:
            logger.warning("Fast start: rounded sell quantity <= 0")
            state.fast_start_active = False
            state.fast_start_completed = True
            save_state(state)
            return state, False

        logger.info("Fast start: target hit, selling %.6f %s @ %.2f", sell_qty, pair, exit_price)
        order_id = data_client.place_order(pair=pair, side="sell", qty=sell_qty, price=exit_price)
        if order_id:
            refreshed_state = data_client.get_positions()
            refreshed_state.fast_start_active = False
            refreshed_state.fast_start_completed = True
            refreshed_state.fast_start_entry_price = None
            refreshed_state.fast_start_target_price = None
            save_state(refreshed_state)
            logger.info("Fast start complete: resuming normal strategy")
            return refreshed_state, True

        logger.error("Fast start: sell order failed, will retry")
        return state, True

    # Still waiting for target; pause the main strategy
    return state, True


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

            state, fast_start_block = maybe_run_fast_start(state, data_client, config)
            if fast_start_block:
                time.sleep(config["exchange"]["rate_limit_ms"] / 1000.0)
                continue
            
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

