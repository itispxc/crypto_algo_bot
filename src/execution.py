"""
Order execution and rebalancing.
"""
import logging
from typing import Dict, List
import time

from .data_classes import PortfolioState, MarketSnapshot
from .data_client import DataClient
from .utils import precision_round, amount_precision_for
from .risk import check_stop_losses

logger = logging.getLogger(__name__)


def rebalance_to_weights(target_w: Dict[str, float],
                        state: PortfolioState,
                        snapshots: Dict[str, MarketSnapshot],
                        data_client: DataClient,
                        config: dict) -> List[str]:
    """
    Rebalance portfolio to target weights.
    
    Args:
        target_w: Target weights by pair
        state: Current portfolio state
        snapshots: Market snapshots
        data_client: Data client for placing orders
        config: Configuration dict
        
    Returns:
        List of order IDs placed
    """
    orders = []
    equity = state.equity
    hyster = config["signals"]["hysteresis_weight_change"]
    min_order_usd = config["exchange"]["min_order_usd"]
    
    exchange_info = data_client.exchange_info or {}
    
    for pair, tw in target_w.items():
        if pair not in snapshots:
            continue
        
        snapshot = snapshots[pair]
        price = snapshot.price
        bid = snapshot.bid
        ask = snapshot.ask
        
        # Current position
        pos = state.positions.get(pair)
        cur_qty = pos.quantity if pos else 0.0
        cur_val = cur_qty * price
        cur_w = cur_val / max(equity, 1e-6)
        
        # Check hysteresis
        if abs(tw - cur_w) < hyster:
            continue
        
        # Calculate target USD and delta
        usd_target = tw * equity
        delta_usd = usd_target - cur_val
        
        if abs(delta_usd) < min_order_usd:
            continue
        
        # Calculate quantity
        qty = delta_usd / price
        amount_prec = amount_precision_for(pair, exchange_info)
        qty = precision_round(qty, amount_prec)
        
        if qty == 0:
            continue
        
        # Determine side
        side = "buy" if qty > 0 else "sell"
        qty_abs = abs(qty)
        
        # Place limit order near mid
        if side == "buy":
            order_price = min(ask, (bid + ask) / 2 + 0.5 * (ask - bid))
        else:
            order_price = max(bid, (bid + ask) / 2 - 0.5 * (ask - bid))
        
        try:
            order_id = data_client.place_order(
                pair=pair,
                side=side,
                qty=qty_abs,
                price=order_price,
                order_type="limit"
            )
            if order_id:
                orders.append(order_id)
                logger.info(f"Placed {side} order: {qty_abs} {pair} @ {order_price}")
        except Exception as e:
            logger.error(f"Failed to place order for {pair}: {e}")
    
    return orders


def apply_stops_and_tps(state: PortfolioState,
                       snapshots: Dict[str, MarketSnapshot],
                       data_client: DataClient,
                       config: dict) -> List[str]:
    """
    Apply stop losses and take profits.
    
    Args:
        state: Portfolio state
        snapshots: Market snapshots
        data_client: Data client
        config: Configuration dict
        
    Returns:
        List of order IDs placed
    """
    orders = []
    to_sell = check_stop_losses(state, snapshots, config)
    
    for pair, qty in to_sell.items():
        if pair not in snapshots:
            continue
        
        snapshot = snapshots[pair]
        try:
            order_id = data_client.place_order(
                pair=pair,
                side="sell",
                qty=qty,
                price=snapshot.bid,
                order_type="market"
            )
            if order_id:
                orders.append(order_id)
                logger.info(f"Stop loss executed: {qty} {pair}")
        except Exception as e:
            logger.error(f"Failed to execute stop for {pair}: {e}")
    
    return orders

