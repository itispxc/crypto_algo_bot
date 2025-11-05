"""
Performance metrics calculation.
"""
import numpy as np
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def compute_intraday_metrics(pnl_series: List[float]) -> Dict[str, float]:
    """
    Compute intraday performance metrics.
    
    Args:
        pnl_series: Series of PnL values
        
    Returns:
        Dictionary of metrics
    """
    if len(pnl_series) < 2:
        return {
            "sharpe": 0.0,
            "sortino": 0.0,
            "calmar": 0.0,
            "mdd": 0.0
        }
    
    arr = np.array(pnl_series)
    returns = np.diff(arr) / (arr[:-1] + 1e-8)
    
    mean_ret = np.mean(returns)
    std_ret = np.std(returns)
    
    # Sharpe ratio
    sharpe = (mean_ret / std_ret * np.sqrt(252 * 96)) if std_ret > 0 else 0.0
    
    # Sortino ratio (downside deviation)
    negative_returns = returns[returns < 0]
    downside_std = np.std(negative_returns) if len(negative_returns) > 0 else std_ret
    sortino = (mean_ret / downside_std * np.sqrt(252 * 96)) if downside_std > 0 else 0.0
    
    # Maximum drawdown
    running_max = np.maximum.accumulate(arr)
    drawdowns = (arr - running_max) / (running_max + 1e-8)
    mdd = float(np.min(drawdowns))
    
    # Calmar ratio (mean return / |MDD|)
    calmar = mean_ret / abs(mdd) if mdd != 0 else 0.0
    calmar = calmar * np.sqrt(252 * 96)  # Annualize
    
    return {
        "sharpe": float(sharpe),
        "sortino": float(sortino),
        "calmar": float(calmar),
        "mdd": float(mdd)
    }

