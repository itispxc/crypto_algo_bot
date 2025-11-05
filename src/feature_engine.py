"""
Feature engineering for trading signals.
"""
import numpy as np
from typing import Dict, List
import logging

from .data_classes import Candle
from .utils import ema, rsi, bb_percent, infer_tier

logger = logging.getLogger(__name__)


def compute_features(c5: Dict[str, List[Candle]], 
                    c30: Dict[str, List[Candle]],
                    config: dict) -> Dict[str, Dict[str, float]]:
    """
    Compute features for all pairs.
    
    Args:
        c5: 5-minute candles by pair
        c30: 30-minute candles by pair
        config: Configuration dict
        
    Returns:
        Dictionary mapping pair to feature dict
    """
    features = {}
    
    for pair in c5.keys():
        try:
            candles_5m = c5.get(pair, [])
            candles_30m = c30.get(pair, [])
            
            if len(candles_5m) < 288 or len(candles_30m) < 48:
                logger.warning(f"Insufficient data for {pair}")
                continue
            
            feat = _compute_pair_features(candles_5m, candles_30m, pair, config)
            features[pair] = feat
            
        except Exception as e:
            logger.error(f"Error computing features for {pair}: {e}")
            continue
    
    return features


def _compute_pair_features(candles_5m: List[Candle], 
                          candles_30m: List[Candle],
                          pair: str,
                          config: dict) -> Dict[str, float]:
    """Compute features for a single pair."""
    closes5 = np.array([c.close for c in candles_5m])
    closes30 = np.array([c.close for c in candles_30m])
    
    # Returns
    rets5 = np.diff(np.log(closes5))
    
    # Momentum features
    r_1h = np.exp(rets5[-12:].sum()) - 1 if len(rets5) >= 12 else 0.0
    r_3h = np.exp(rets5[-36:].sum()) - 1 if len(rets5) >= 36 else 0.0
    r_6h = np.exp(rets5[-72:].sum()) - 1 if len(rets5) >= 72 else 0.0
    r_24h = np.exp(rets5[-288:].sum()) - 1 if len(rets5) >= 288 else 0.0
    
    # Mean reversion features
    ema20 = ema(closes5, 20)
    ema60 = ema(closes5, 60)
    
    if len(ema20) >= 96:
        resid = closes5 - ema20
        ema20_z = (closes5[-1] - ema20[-1]) / (np.std(resid[-96:]) + 1e-8)
    else:
        ema20_z = 0.0
    
    if len(ema60) >= 288:
        resid60 = closes5 - ema60
        ema60_z = (closes5[-1] - ema60[-1]) / (np.std(resid60[-288:]) + 1e-8)
    else:
        ema60_z = 0.0
    
    rsi7 = rsi(closes5, 7)
    rsi14 = rsi(closes5, 14)
    bb_pos = bb_percent(closes5, 20, 2.0)
    
    # Volatility features
    if len(closes30) >= 48:
        rets30 = np.diff(np.log(closes30))
        rv_24h = np.std(rets30[-48:]) * np.sqrt(48) if len(rets30) >= 48 else 0.05
    else:
        rv_24h = 0.05
    
    if len(rets5) >= 72:
        rv_6h = np.std(rets5[-72:]) * np.sqrt(72) if len(rets5) >= 72 else 0.05
    else:
        rv_6h = 0.05
    
    atr_14_30m = _compute_atr(candles_30m, 14)
    
    # Drawdown from peak
    if len(closes30) >= 48:
        rolling_max = np.maximum.accumulate(closes30[-48:])
        dd_from_peak = (closes30[-1] / rolling_max[-1]) - 1 if rolling_max[-1] > 0 else 0.0
    else:
        dd_from_peak = 0.0
    
    # Tier
    tier = infer_tier(pair, config)
    
    return {
        "r_1h": float(r_1h),
        "r_3h": float(r_3h),
        "r_6h": float(r_6h),
        "r_24h": float(r_24h),
        "ema20_z": float(ema20_z),
        "ema60_z": float(ema60_z),
        "rsi7": float(rsi7),
        "rsi14": float(rsi14),
        "bb_pos": float(bb_pos),
        "rv_6h": float(rv_6h),
        "rv_24h": float(rv_24h),
        "atr_14_30m": float(atr_14_30m),
        "dd_from_peak": float(dd_from_peak),
        "tier": tier
    }


def _compute_atr(candles: List[Candle], period: int) -> float:
    """Compute Average True Range."""
    if len(candles) < period + 1:
        return 0.0
    
    true_ranges = []
    for i in range(1, len(candles)):
        tr = max(
            candles[i].high - candles[i].low,
            abs(candles[i].high - candles[i-1].close),
            abs(candles[i].low - candles[i-1].close)
        )
        true_ranges.append(tr)
    
    if len(true_ranges) >= period:
        return float(np.mean(true_ranges[-period:]))
    return 0.0


def compute_atr_30m(pairs: List[str], 
                   candles_30m: Dict[str, List[Candle]]) -> Dict[str, float]:
    """
    Compute ATR for all pairs from 30m candles.
    
    Args:
        pairs: List of trading pairs
        candles_30m: 30-minute candles by pair
        
    Returns:
        Dictionary mapping pair to ATR
    """
    atrs = {}
    for pair in pairs:
        if pair in candles_30m:
            atrs[pair] = _compute_atr(candles_30m[pair], 14)
        else:
            atrs[pair] = 0.0
    return atrs

