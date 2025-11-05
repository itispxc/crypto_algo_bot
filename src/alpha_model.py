"""
Alpha model using LightGBM for signal scoring.
"""
import os
import numpy as np
from typing import Dict, List
import logging

# Try to import lightgbm, but handle if not available
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except (ImportError, OSError, Exception):
    LIGHTGBM_AVAILABLE = False
    lgb = None

from .data_classes import Signal
logger = logging.getLogger(__name__)


def load_models(config: dict) -> Dict[str, any]:
    """
    Load trained models.
    
    Args:
        config: Configuration dict
        
    Returns:
        Dictionary mapping horizon to model
    """
    models = {}
    model_dir = "models"
    
    if not LIGHTGBM_AVAILABLE:
        logger.warning("LightGBM not available - models will use fallback scoring")
        return {"6h": None, "24h": None}
    
    # Try to load 6h and 24h models
    for horizon in ["6h", "24h"]:
        model_path = os.path.join(model_dir, f"lgbm_{horizon}.txt")
        if os.path.exists(model_path):
            try:
                models[horizon] = lgb.Booster(model_file=model_path)
                logger.info(f"Loaded model: {horizon}")
            except Exception as e:
                logger.error(f"Failed to load model {horizon}: {e}")
                models[horizon] = None
        else:
            logger.warning(f"Model file not found: {model_path}")
            models[horizon] = None
    
    return models


def score_signals(models: Dict[str, any],
                 features: Dict[str, Dict[str, float]],
                 regime_info: Dict[str, any],
                 config: dict) -> Dict[str, Signal]:
    """
    Score signals for all pairs.
    
    Args:
        models: Dictionary of models by horizon
        features: Features by pair
        regime_info: Market regime information
        config: Configuration dict
        
    Returns:
        Dictionary mapping pair to Signal
    """
    signals = {}
    
    # Feature order (must match training)
    feature_order = [
        "r_1h", "r_3h", "r_6h", "r_24h",
        "ema20_z", "ema60_z", "rsi7", "rsi14", "bb_pos",
        "rv_6h", "rv_24h", "atr_14_30m", "dd_from_peak"
    ]
    
    for pair, feat in features.items():
        try:
            # Build feature vector
            x = np.array([feat.get(k, 0.0) for k in feature_order], dtype=float)
            
            # Get predictions
            p6 = 0.0
            p24 = 0.0
            
            # Get predictions (with fallback if models not available)
            if models.get("6h") and LIGHTGBM_AVAILABLE and models["6h"] is not None:
                try:
                    p6 = models["6h"].predict(x.reshape(1, -1))[0]
                except:
                    # Fallback: use simple feature-based scoring
                    p6 = feat.get('r_6h', 0) * 0.5 + (feat.get('rsi14', 50) / 100 - 0.5) * 0.3
            else:
                # Fallback scoring when models not available
                p6 = feat.get('r_6h', 0) * 0.5 + (feat.get('rsi14', 50) / 100 - 0.5) * 0.3
            
            if models.get("24h") and LIGHTGBM_AVAILABLE and models.get("24h") is not None:
                try:
                    p24 = models["24h"].predict(x.reshape(1, -1))[0]
                except:
                    # Fallback
                    p24 = feat.get('r_24h', 0) * 0.5 + (feat.get('rsi14', 50) / 100 - 0.5) * 0.3
            else:
                # Fallback scoring
                p24 = feat.get('r_24h', 0) * 0.5 + (feat.get('rsi14', 50) / 100 - 0.5) * 0.3
            
            # Weight by regime
            regime = regime_info.get("regime", "chop")
            if regime == "chop":
                w6, w24 = 0.6, 0.4
            else:
                w6, w24 = 0.3, 0.7
            
            # Combine predictions
            s = w6 * p6 + w24 * p24
            
            # Account for costs
            fee_bps = config["exchange"]["fee_bps"]
            fees = 2 * (fee_bps / 10000.0)  # Round trip
            slippage = 0.0003  # 3 bps estimated slippage
            exp_net = s - (fees + slippage)
            
            # Get volatility
            vol = feat.get("rv_24h", 0.05)
            tier = feat.get("tier", 1)
            
            signals[pair] = Signal(
                pair=pair,
                score=float(s),
                exp_ret_net=float(exp_net),
                vol=float(vol),
                tier=int(tier)
            )
            
        except Exception as e:
            logger.error(f"Error scoring {pair}: {e}")
            continue
    
    return signals


def create_dummy_models():
    """
    Create dummy models if real models don't exist.
    For testing purposes only.
    """
    logger.warning("Creating dummy models - replace with trained models for production!")
    return {
        "6h": None,
        "24h": None
    }

