"""
Utility functions for precision, calculations, and helpers.
"""
import numpy as np
from typing import List


def precision_round(value: float, precision: int) -> float:
    """
    Round value to specified number of decimal places.
    
    Args:
        value: Value to round
        precision: Number of decimal places
        
    Returns:
        Rounded value
    """
    if precision == 0:
        return float(int(value))
    multiplier = 10 ** precision
    return float(int(value * multiplier) / multiplier)


def annualize_vol(std_15m: float) -> float:
    """
    Annualize volatility from 15-minute standard deviation.
    
    Args:
        std_15m: Standard deviation of 15-minute returns
        
    Returns:
        Annualized volatility
    """
    # 15 minutes = 0.25 hours = 1/96 of a day
    # Annualize: std_daily * sqrt(365)
    # std_daily = std_15m * sqrt(96)
    return std_15m * np.sqrt(96 * 365)


def zscore(series: List[float]) -> float:
    """
    Calculate z-score of last value in series.
    
    Args:
        series: List of values
        
    Returns:
        Z-score of last value
    """
    if len(series) < 2:
        return 0.0
    arr = np.array(series)
    mean = np.mean(arr)
    std = np.std(arr)
    if std == 0:
        return 0.0
    return (arr[-1] - mean) / std


def ema(values: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Exponential Moving Average.
    
    Args:
        values: Array of values
        period: EMA period
        
    Returns:
        Array of EMA values
    """
    if len(values) == 0:
        return np.array([])
    alpha = 2.0 / (period + 1)
    result = np.zeros_like(values)
    result[0] = values[0]
    for i in range(1, len(values)):
        result[i] = alpha * values[i] + (1 - alpha) * result[i-1]
    return result


def rsi(values: np.ndarray, period: int) -> float:
    """
    Calculate Relative Strength Index.
    
    Args:
        values: Array of prices
        period: RSI period
        
    Returns:
        RSI value (0-100)
    """
    if len(values) < period + 1:
        return 50.0
    
    deltas = np.diff(values)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi_value = 100 - (100 / (1 + rs))
    return float(rsi_value)


def bb_percent(values: np.ndarray, period: int, std_dev: float) -> float:
    """
    Calculate Bollinger Band position (0-1).
    
    Args:
        values: Array of prices
        period: BB period
        std_dev: Standard deviation multiplier
        
    Returns:
        Position in BB (0=lower, 1=upper, 0.5=middle)
    """
    if len(values) < period:
        return 0.5
    
    recent = values[-period:]
    mean = np.mean(recent)
    std = np.std(recent)
    
    if std == 0:
        return 0.5
    
    upper = mean + std_dev * std
    lower = mean - std_dev * std
    
    if upper == lower:
        return 0.5
    
    current = values[-1]
    position = (current - lower) / (upper - lower)
    return float(np.clip(position, 0.0, 1.0))


def infer_tier(pair: str, config: dict) -> int:
    """
    Infer tier from pair name.
    
    Args:
        pair: Trading pair
        config: Configuration dict
        
    Returns:
        Tier (1, 2, or 3)
    """
    if pair in config.get("universe", {}).get("tier1", []):
        return 1
    elif pair in config.get("universe", {}).get("tier2", []):
        return 2
    elif pair in config.get("universe", {}).get("tier3", []):
        return 3
    return 1  # Default to tier 1


def amount_precision_for(pair: str, exchange_info: dict) -> int:
    """
    Get amount precision for a trading pair.
    
    Args:
        pair: Trading pair
        exchange_info: Exchange info from API
        
    Returns:
        Amount precision (decimal places)
    """
    # Default precision if not found
    default_precision = 5
    
    trade_pairs = exchange_info.get("TradePairs", {})
    pair_info = trade_pairs.get(pair, {})
    return pair_info.get("AmountPrecision", default_precision)


def price_precision_for(pair: str, exchange_info: dict) -> int:
    """
    Get price precision for a trading pair.
    
    Args:
        pair: Trading pair
        exchange_info: Exchange info from API
        
    Returns:
        Price precision (decimal places)
    """
    # Default precision if not found
    default_precision = 2
    
    trade_pairs = exchange_info.get("TradePairs", {})
    pair_info = trade_pairs.get(pair, {})
    return pair_info.get("PricePrecision", default_precision)

