"""
Data classes for trading bot.
"""
from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class Candle:
    """Candlestick/OHLCV data."""
    ts: int  # epoch milliseconds
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class MarketSnapshot:
    """Market snapshot data."""
    pair: str
    price: float
    bid: float
    ask: float
    vol24h: float


@dataclass
class Position:
    """Position data."""
    pair: str
    quantity: float
    avg_price: float
    usd_value: float
    stop_price: Optional[float] = None
    trail_anchor: Optional[float] = None


@dataclass
class PortfolioState:
    """Portfolio state."""
    cash_usd: float
    positions: Dict[str, Position]
    equity: float
    peak_equity: float
    last_rebalance_ts: int


@dataclass
class Signal:
    """Trading signal."""
    pair: str
    score: float
    exp_ret_net: float
    vol: float
    tier: int

