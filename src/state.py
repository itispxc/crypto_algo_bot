"""
Portfolio state persistence.
"""
import json
import os
import logging
from typing import Optional

from .data_classes import PortfolioState, Position

logger = logging.getLogger(__name__)

STATE_FILE = "state.json"


def load_state() -> PortfolioState:
    """
    Load portfolio state from disk.
    
    Returns:
        PortfolioState
    """
    if not os.path.exists(STATE_FILE):
        return PortfolioState(
            cash_usd=0.0,
            positions={},
            equity=0.0,
            peak_equity=0.0,
            last_rebalance_ts=0
        )
    
    try:
        with open(STATE_FILE, 'r') as f:
            data = json.load(f)
        
        # Reconstruct positions
        positions = {}
        for pair, pos_data in data.get("positions", {}).items():
            positions[pair] = Position(**pos_data)
        
        return PortfolioState(
            cash_usd=data.get("cash_usd", 0.0),
            positions=positions,
            equity=data.get("equity", 0.0),
            peak_equity=data.get("peak_equity", 0.0),
            last_rebalance_ts=data.get("last_rebalance_ts", 0),
            fast_start_active=data.get("fast_start_active", False),
            fast_start_completed=data.get("fast_start_completed", False),
            fast_start_entry_price=data.get("fast_start_entry_price"),
            fast_start_target_price=data.get("fast_start_target_price")
        )
    except Exception as e:
        logger.error(f"Failed to load state: {e}")
        return PortfolioState(
            cash_usd=0.0,
            positions={},
            equity=0.0,
            peak_equity=0.0,
            last_rebalance_ts=0
        )


def save_state(state: PortfolioState):
    """
    Save portfolio state to disk.
    
    Args:
        state: PortfolioState to save
    """
    try:
        # Convert positions to dict
        positions_dict = {}
        for pair, pos in state.positions.items():
            positions_dict[pair] = {
                "pair": pos.pair,
                "quantity": pos.quantity,
                "avg_price": pos.avg_price,
                "usd_value": pos.usd_value,
                "stop_price": pos.stop_price,
                "trail_anchor": pos.trail_anchor
            }
        
        data = {
            "cash_usd": state.cash_usd,
            "positions": positions_dict,
            "equity": state.equity,
            "peak_equity": state.peak_equity,
            "last_rebalance_ts": state.last_rebalance_ts,
            "fast_start_active": state.fast_start_active,
            "fast_start_completed": state.fast_start_completed,
            "fast_start_entry_price": state.fast_start_entry_price,
            "fast_start_target_price": state.fast_start_target_price
        }
        
        with open(STATE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.debug("State saved")
    except Exception as e:
        logger.error(f"Failed to save state: {e}")


def track_peak_equity(state: PortfolioState):
    """
    Update peak equity.
    
    Args:
        state: Portfolio state
    """
    if state.equity > state.peak_equity:
        state.peak_equity = state.equity

