"""
Portfolio construction and weight management.
"""
import numpy as np
from typing import Dict
import logging

from .data_classes import Signal, PortfolioState

logger = logging.getLogger(__name__)


def build_target_weights(signals: Dict[str, Signal],
                        regime_info: Dict[str, any],
                        state: PortfolioState,
                        config: dict) -> Dict[str, float]:
    """
    Build target portfolio weights.
    
    Args:
        signals: Signals by pair
        regime_info: Market regime information
        state: Current portfolio state
        config: Configuration dict
        
    Returns:
        Dictionary mapping pair to target weight
    """
    # Filter by score threshold
    sig_list = [
        v for v in signals.values() 
        if v.exp_ret_net > config["signals"]["score_threshold"]
    ]
    
    if not sig_list:
        return {}
    
    # Select top-k by regime
    regime = regime_info.get("regime", "trend")
    if regime == "down":
        top_k = config["signals"]["top_k_down"]
    elif regime == "chop":
        top_k = config["signals"]["top_k_chop"]
    else:
        top_k = config["signals"]["top_k_normal"]
    
    # Sort by score
    sig_list.sort(key=lambda s: s.score, reverse=True)
    selected = sig_list[:top_k]
    
    # Size inverse-vol and score-tilt
    raw_weights = []
    for sig in selected:
        vol = max(sig.vol, 1e-3)  # Avoid division by zero
        w = sig.score / vol
        raw_weights.append((sig.pair, w, sig.tier))
    
    # Normalize to 1 - cash buffer
    cb_key = regime if regime in ("down", "chop") else "normal"
    cash_buffer_map = {
        "down": config["sizing"]["cash_buffer_down"],
        "chop": config["sizing"]["cash_buffer_chop"],
        "normal": config["sizing"]["cash_buffer_normal"]
    }
    cb = cash_buffer_map.get(cb_key, 0.1)
    
    total_raw = sum(max(0.0, r[1]) for r in raw_weights) or 1.0
    
    # Build target weights with caps
    w_target = {}
    t3_sum = 0.0
    t3_cap = config["sizing"]["sleeve_t3_max"]
    
    for pair, w, tier in raw_weights:
        w_n = (1 - cb) * w / total_raw
        
        # Apply tier caps
        if tier == 1:
            cap = config["sizing"]["cap_t1"]
        elif tier == 2:
            cap = config["sizing"]["cap_t2"]
        else:
            cap = config["sizing"]["cap_t3"]
        
        w_n = min(w_n, cap)
        
        # Tier 3 sleeve cap
        if tier == 3:
            if t3_sum + w_n > t3_cap:
                w_n = max(0.0, t3_cap - t3_sum)
            t3_sum += w_n
        
        w_target[pair] = w_n
    
    return w_target


def scale_weights(w_target: Dict[str, float], scalar: float) -> Dict[str, float]:
    """
    Scale weights by exposure scalar.
    
    Args:
        w_target: Target weights
        scalar: Exposure scalar (0-1)
        
    Returns:
        Scaled weights
    """
    return {k: v * scalar for k, v in w_target.items()}


def mark_to_market(state: PortfolioState, 
                  snapshots: Dict[str, any]) -> PortfolioState:
    """
    Mark positions to market.
    
    Args:
        state: Current portfolio state
        snapshots: Market snapshots by pair
        
    Returns:
        Updated portfolio state
    """
    equity = state.cash_usd
    
    for pair, pos in state.positions.items():
        if pair in snapshots:
            price = snapshots[pair].price
            pos.usd_value = pos.quantity * price
            equity += pos.usd_value
    
    state.equity = equity
    state.peak_equity = max(state.peak_equity, equity)
    
    return state

