"""
Market regime detection.
"""
import numpy as np
from typing import List, Dict
import logging

from .data_classes import Candle
from .utils import ema

logger = logging.getLogger(__name__)


def compute_market_regime(btc_30m: List[Candle]) -> Dict[str, any]:
    """
    Compute market regime based on BTC 30m data.
    
    Args:
        btc_30m: BTC 30-minute candles
        
    Returns:
        Regime dictionary with regime, vol_regime, and breadth
    """
    if len(btc_30m) < 200:
        return {
            "regime": "chop",
            "vol_regime": "mid",
            "breadth": 0.5
        }
    
    closes = np.array([c.close for c in btc_30m])
    
    # Compute EMAs
    ema50 = ema(closes, 50)
    ema200 = ema(closes, 200)
    
    if len(ema50) < 5:
        return {
            "regime": "chop",
            "vol_regime": "mid",
            "breadth": 0.5
        }
    
    # Determine regime
    slope = ema50[-1] - ema50[-5] if len(ema50) > 5 else 0.0
    
    if ema50[-1] > ema200[-1] and slope > 0:
        regime = "trend"
    elif ema50[-1] < ema200[-1] and slope < 0:
        regime = "down"
    else:
        regime = "chop"
    
    # Volatility regime
    if len(closes) >= 96:
        rets = np.diff(np.log(closes[-96:]))
        rv = np.std(rets) * np.sqrt(96)
    else:
        rv = 0.4
    
    if rv > 0.8:
        vol_regime = "high"
    elif rv > 0.4:
        vol_regime = "mid"
    else:
        vol_regime = "low"
    
    # Breadth (placeholder - would need cross-section data)
    # For now, use BTC momentum as proxy
    if len(closes) >= 48:
        r_24h = (closes[-1] / closes[-48]) - 1 if closes[-48] > 0 else 0.0
        breadth = 0.5 + min(0.5, max(-0.5, r_24h * 2))  # Proxy breadth
    else:
        breadth = 0.5
    
    return {
        "regime": regime,
        "vol_regime": vol_regime,
        "breadth": float(breadth)
    }

