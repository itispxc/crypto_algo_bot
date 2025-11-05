"""
Risk management and stop loss logic.
"""
from typing import Dict, Optional
import logging

from .data_classes import PortfolioState, Position, MarketSnapshot

logger = logging.getLogger(__name__)


def update_stops(state: PortfolioState,
                atr_by_pair: Dict[str, float],
                snapshots: Dict[str, MarketSnapshot],
                regime_info: Optional[Dict] = None,
                config: dict = None) -> PortfolioState:
    """
    Update stop loss prices for positions.
    
    Args:
        state: Portfolio state
        atr_by_pair: ATR values by pair
        regime_info: Market regime (optional)
        config: Configuration dict
        
    Returns:
        Updated portfolio state
    """
    if not config:
        return state
    
    atr_init = config["stops"]["atr_init"]
    atr_trail = config["stops"]["atr_trail"]
    
    for pair, pos in state.positions.items():
        if pos.quantity <= 0:
            continue
        
        atr = atr_by_pair.get(pair, 0.0)
        if atr == 0:
            continue
        
        # Initial stop
        if pos.stop_price is None:
            pos.stop_price = pos.avg_price - atr_init * atr
            pos.trail_anchor = None
        
        # Trailing stop logic
        # Get current price from snapshot
        if pair in snapshots:
            current_price = snapshots[pair].price
        else:
            current_price = pos.avg_price  # Fallback
        
        # If price moved up by 0.8*ATR, set trail anchor
        if pos.trail_anchor is None:
            if current_price >= pos.avg_price + 0.8 * atr:
                pos.trail_anchor = current_price
        else:
            # Update trail anchor if price moves higher
            if current_price > pos.trail_anchor:
                pos.trail_anchor = current_price
            
            # Update trailing stop
            if pos.trail_anchor:
                pos.stop_price = pos.trail_anchor - atr_trail * atr
    
    return state


def check_drawdown_and_scale(state: PortfolioState, config: dict) -> float:
    """
    Check drawdown and return exposure scalar.
    
    Args:
        state: Portfolio state
        config: Configuration dict
        
    Returns:
        Exposure scalar (0-1)
    """
    if state.peak_equity == 0:
        return 1.0
    
    dd = (state.equity - state.peak_equity) / state.peak_equity
    
    soft_dd = -config["risk"]["soft_dd"]
    hard_dd = -config["risk"]["hard_dd"]
    
    if dd < hard_dd:
        logger.warning(f"Hard drawdown hit: {dd:.2%}, scaling to 0.2")
        return 0.2
    elif dd < soft_dd:
        reduce_factor = config["risk"]["reduce_after_soft"]
        logger.warning(f"Soft drawdown hit: {dd:.2%}, scaling to {reduce_factor}")
        return reduce_factor
    else:
        return 1.0


def check_stop_losses(state: PortfolioState,
                     snapshots: Dict[str, MarketSnapshot],
                     config: dict) -> Dict[str, float]:
    """
    Check if any positions hit stop loss.
    
    Args:
        state: Portfolio state
        snapshots: Market snapshots
        config: Configuration dict
        
    Returns:
        Dictionary of pairs to sell (quantity)
    """
    to_sell = {}
    max_loss_portion = config["stops"]["max_pos_loss_portion"]
    
    for pair, pos in state.positions.items():
        if pair not in snapshots:
            continue
        
        price = snapshots[pair].price
        
        # Check stop price
        if pos.stop_price and price <= pos.stop_price:
            logger.info(f"Stop loss triggered for {pair}: {price} <= {pos.stop_price}")
            to_sell[pair] = pos.quantity
        
        # Check max position loss
        loss_pct = (price - pos.avg_price) / pos.avg_price
        if loss_pct < -max_loss_portion:
            logger.info(f"Max loss hit for {pair}: {loss_pct:.2%}")
            to_sell[pair] = pos.quantity
    
    return to_sell

