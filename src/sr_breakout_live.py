"""
Live S/R Breakout Strategy for ZEC/USD - 1 minute bars
"""
import time
import math
import logging
from datetime import datetime, timezone
from typing import Optional, Dict
import pandas as pd
import numpy as np

import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.data_client import DataClient
from src.state import load_state, save_state
from src.strategies.sr_breakout import SRBreakoutBacktester, SRBreakoutParams
from src.data_classes import Position

logger = logging.getLogger(__name__)

# Profit target for ZEC/USD trades (4.2%)
PROFIT_TARGET_PCT = 4.2


def _round_to_step(value: float, step: float, direction: str = "nearest") -> float:
    """Align value to exchange step size."""
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


def candles_to_df(candles):
    return pd.DataFrame([
        {
            "timestamp": c.ts,
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume,
        }
        for c in candles
    ])


def run_sr_breakout_live(config: dict):
    """
    Run S/R breakout strategy live on ZEC/USD with 1-minute bars.
    """
    logging.basicConfig(
        level=getattr(logging, config["ops"]["log_level"]),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("=" * 60)
    logger.info("S/R Breakout Strategy - LIVE TRADING")
    logger.info("Pair: ZEC/USD | Interval: 1m")
    logger.info("=" * 60)
    
    pair = "ZEC/USD"
    interval = "1m"
    fee_bps = config["exchange"]["fee_bps"]
    
    # Strategy parameters (from your Pine script)
    # Note: EC2 version doesn't have hold_bars or min_profit_percent
    # Profit target is set as PROFIT_TARGET_PCT constant above
    params = SRBreakoutParams(
        left_bars=6,
        right_bars=9,
        volume_threshold=31.0,
        cooldown_bars=21
    )
    
    data_client = DataClient(config)
    state = load_state()
    
    if state.equity == 0:
        logger.info("Loading initial state from exchange...")
        state = data_client.get_positions()
        save_state(state)
    
    logger.info(f"Initial equity: ${state.equity:,.2f}")
    logger.info(f"Dry run: {config['ops']['dry_run']}")
    
    # Show all positions and wait for BTC to hit 0.2% profit before selling
    logger.info("Checking for existing positions...")
    state = data_client.get_positions()
    
    # Also check raw balance for BTC (in case it's not in positions from orders)
    balance = data_client.client.get_balance()
    if balance.get('Success'):
        spot_wallet = balance.get('SpotWallet', {})
        btc_balance = spot_wallet.get('BTC', {})
        btc_qty = float(btc_balance.get('Free', 0))
        
        if btc_qty > 0 and 'BTC/USD' not in state.positions:
            # Create a position from the raw balance
            logger.info(f"Found BTC in balance: {btc_qty:.6f} (not in tracked positions)")
            snapshot = data_client.get_snapshot('BTC/USD')
            if snapshot:
                # Try to get actual entry price from order history
                entry_price = snapshot.price  # Default to current price
                orders = data_client.client.query_order(pair='BTC/USD', limit=100)
                if orders.get('Success'):
                    order_list = orders.get('OrderMatched', [])
                    # Find most recent BUY order
                    for order in reversed(order_list):
                        if order.get('Side') == 'BUY' and order.get('Status') == 'FILLED':
                            entry_price = float(order.get('FilledAverPrice', entry_price))
                            break
                
                state.positions['BTC/USD'] = Position(
                    pair='BTC/USD',
                    quantity=btc_qty,
                    avg_price=entry_price,
                    usd_value=btc_qty * snapshot.price
                )
                logger.info(f"Created BTC/USD position from balance: {btc_qty:.6f} @ ${entry_price:.2f}")
    
    # Show all positions
    logger.info("\n" + "=" * 80)
    logger.info("CURRENT POSITIONS:")
    logger.info("=" * 80)
    for pos_pair, position in state.positions.items():
        if position.quantity > 0:
            snapshot = data_client.get_snapshot(pos_pair)
            if snapshot:
                current_price = snapshot.price
                entry_price = position.avg_price
                profit_pct = ((current_price - entry_price) / entry_price) * 100
                value = position.quantity * current_price
                logger.info(f"{pos_pair}: {position.quantity:.6f} @ ${entry_price:.2f} | "
                          f"Current: ${current_price:.2f} | Profit: {profit_pct:+.2f}% | Value: ${value:,.2f}")
    logger.info("=" * 80 + "\n")
    
    # Keep BTC position (don't sell it) and start trading ZEC/USD immediately
    logger.info("Starting ZEC/USD trading...")
    logger.info("Note: BTC position will be kept (not sold)")
    
    # Track position
    position_entry_price: Optional[float] = None
    position_entry_time: Optional[datetime] = None
    last_trade_time: Optional[datetime] = None
    last_candle_time: Optional[int] = None
    
    # Get pair filters for order sizing
    pair_filters = data_client.get_pair_filters(pair)
    price_step = pair_filters.get("price_step", 0.01)
    qty_step = pair_filters.get("qty_step", 0.0001)
    min_qty = pair_filters.get("min_qty", 0.0)
    min_notional = pair_filters.get("min_notional", 0.0)
    
    while True:
        try:
            now = datetime.now(timezone.utc)
            
            # Fetch recent candles (need enough for indicators)
            candles = data_client.get_candles(pair, interval, 500)
            if not candles:
                logger.warning("No candles received, waiting...")
                time.sleep(60)
                continue
            
            # Check if we have new data
            latest_candle = candles[-1]
            if last_candle_time and latest_candle.ts <= last_candle_time:
                # No new candle yet
                time.sleep(10)
                continue
            
            last_candle_time = latest_candle.ts
            
            # Convert to DataFrame
            df = candles_to_df(candles)
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            
            # Run backtester to get signals (but we'll execute manually)
            backtester = SRBreakoutBacktester(df, fee_bps=fee_bps)
            
            # Get current price
            snapshot = data_client.get_snapshot(pair)
            if not snapshot:
                logger.warning("No snapshot available")
                time.sleep(10)
                continue
            
            current_price = snapshot.price
            current_time = now
            
            # Update state
            state = data_client.get_positions()
            
            # Check if we have an open position
            open_position = state.positions.get(pair)
            has_position = open_position and open_position.quantity > 0
            
            if has_position:
                # We have a position - check for exit
                if position_entry_price is None:
                    # Load from state
                    position_entry_price = open_position.avg_price
                    logger.info(f"Detected existing position: {open_position.quantity} @ ${position_entry_price:.2f}")
                
                profit_pct = ((current_price - position_entry_price) / position_entry_price) * 100
                
                logger.info(f"Position: {open_position.quantity:.6f} @ ${position_entry_price:.2f} | "
                          f"Current: ${current_price:.2f} | Profit: {profit_pct:.2f}%")
                
                # Check exit condition
                if profit_pct >= PROFIT_TARGET_PCT:
                    # Exit at current price
                    exit_qty = open_position.quantity
                    exit_qty = _round_to_step(exit_qty, qty_step, "floor")
                    exit_price = _round_to_step(current_price, price_step, "floor")
                    
                    if exit_qty > 0 and exit_qty >= min_qty:
                        logger.info(f"PROFIT TARGET HIT! Exiting {exit_qty:.6f} @ ${exit_price:.2f}")
                        order_id = data_client.place_order(
                            pair=pair,
                            side="sell",
                            qty=exit_qty,
                            price=exit_price
                        )
                        if order_id:
                            logger.info(f"Exit order placed: {order_id}")
                            position_entry_price = None
                            position_entry_time = None
                            last_trade_time = current_time
                            time.sleep(5)  # Wait for order to fill
                            continue
                        else:
                            logger.error("Failed to place exit order")
            
            # Check for entry signal
            if not has_position:
                # Need enough candles for indicators
                if len(df) < 250:
                    logger.warning(f"Not enough candles ({len(df)}), need 250+")
                    time.sleep(60)
                    continue
                
                # Run strategy to detect breakout
                result = backtester.run(params)
                
                # Get the last few rows to check for breakout
                df_with_signals = backtester.df.copy()
                pivot_high_raw = SRBreakoutBacktester._pivot_high(df_with_signals["high"], params.left_bars, params.right_bars)
                df_with_signals["pivot_high"] = pivot_high_raw.shift(1).ffill()
                
                # Calculate indicators
                df_with_signals["ema200"] = df_with_signals["close"].ewm(span=200, adjust=False).mean()
                df_with_signals["ema20"] = df_with_signals["close"].ewm(span=20, adjust=False).mean()
                vol = df_with_signals["volume"]
                df_with_signals["vol_ema5"] = vol.ewm(span=5, adjust=False).mean()
                df_with_signals["vol_ema10"] = vol.ewm(span=10, adjust=False).mean()
                
                # Check last bar for breakout
                last_row = df_with_signals.iloc[-1]
                prev_row = df_with_signals.iloc[-2] if len(df_with_signals) > 1 else last_row
                
                resistance = last_row["pivot_high"]
                if not np.isnan(resistance):
                    trend = last_row["close"] > last_row["ema200"]
                    vol_osc = 100 * (last_row["vol_ema5"] - last_row["vol_ema10"]) / max(last_row["vol_ema10"], 1e-9)
                    
                    breakout_above = (
                        trend
                        and last_row["close"] > resistance
                        and prev_row["close"] <= resistance
                        and (vol_osc > params.volume_threshold or last_row["close"] > last_row["ema20"])
                    )
                    
                    # Check cooldown
                    can_trade = True
                    if last_trade_time:
                        minutes_since = (current_time - last_trade_time).total_seconds() / 60
                        can_trade = minutes_since >= params.cooldown_bars
                    
                    if breakout_above and can_trade:
                        # ENTRY SIGNAL!
                        usable_cash = max(0.0, state.cash_usd - 50)  # Keep $50 reserve
                        if usable_cash < config["exchange"]["min_order_usd"]:
                            logger.warning(f"Insufficient cash: ${usable_cash:.2f}")
                        else:
                            entry_price = _round_to_step(current_price, price_step, "ceil")
                            qty = (usable_cash * (1 - fee_bps / 10000.0)) / entry_price
                            qty = _round_to_step(qty, qty_step, "floor")
                            
                            if qty >= min_qty and (qty * entry_price) >= min_notional:
                                logger.info(f"BREAKOUT DETECTED! Buying {qty:.6f} @ ${entry_price:.2f}")
                                order_id = data_client.place_order(
                                    pair=pair,
                                    side="buy",
                                    qty=qty,
                                    price=entry_price
                                )
                                if order_id:
                                    logger.info(f"Entry order placed: {order_id}")
                                    position_entry_price = entry_price
                                    position_entry_time = current_time
                                    last_trade_time = current_time
                                    time.sleep(5)  # Wait for order to fill
                                else:
                                    logger.error("Failed to place entry order")
                            else:
                                logger.warning(f"Quantity too small: {qty:.6f} (min: {min_qty})")
            
            # Log status every minute (show all positions including BTC)
            logger.info(f"Status: ZEC Price=${current_price:.2f} | Cash=${state.cash_usd:.2f} | Equity=${state.equity:.2f}")
            # Show all positions
            for pos_pair, position in state.positions.items():
                if position.quantity > 0:
                    pos_snapshot = data_client.get_snapshot(pos_pair)
                    if pos_snapshot:
                        pos_profit = ((pos_snapshot.price - position.avg_price) / position.avg_price) * 100
                        logger.info(f"  {pos_pair}: {position.quantity:.6f} @ ${position.avg_price:.2f} | "
                                  f"Current: ${pos_snapshot.price:.2f} | Profit: {pos_profit:+.2f}%")
            
            # Wait for next minute
            time.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("Strategy stopped by user")
            save_state(state)
            break
        except Exception as e:
            logger.exception(f"Error in main loop: {e}")
            time.sleep(60)

