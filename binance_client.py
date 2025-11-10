"""
Lightweight client for fetching market data from Binance's public REST API.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional

import requests

logger = logging.getLogger(__name__)


class BinanceClient:
    """Wrapper for the Binance market data REST endpoints we use."""

    def __init__(
        self,
        base_url: str,
        timeout: int = 10,
        candles_endpoint: str = "/api/v3/klines",
        interval_map: Optional[Dict[str, str]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.candles_endpoint = candles_endpoint
        self.interval_map = interval_map or {}
        self.session = requests.Session()

    def get_candles(
        self, symbol: str, interval: str = "5m", limit: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Fetch OHLCV candles from Binance.

        Args:
            symbol: Binance symbol (e.g. BTCUSDT)
            interval: Interval in our internal notation (e.g. 5m, 30m)
            limit: Number of candles requested
        """
        if not self.base_url or not self.candles_endpoint:
            return []

        mapped_interval = self.interval_map.get(interval, interval)
        url = f"{self.base_url}{self.candles_endpoint}"
        params = {
            "symbol": symbol,
            "interval": mapped_interval,
            "limit": limit,
        }

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
        except Exception as exc:
            logger.warning(f"Binance request failed for {symbol}: {exc}")
            return []

        try:
            payload = response.json()
        except ValueError:
            logger.warning("Failed to decode Binance response as JSON.")
            return []

        if not isinstance(payload, list):
            logger.warning("Unexpected Binance payload format.")
            return []

        candles: List[Dict[str, Any]] = []
        for row in payload:
            if not isinstance(row, (list, tuple)) or len(row) < 6:
                continue
            open_time, open_, high, low, close, volume = row[:6]
            try:
                open_time = int(open_time)
                candles.append(
                    {
                        "timestamp": open_time,
                        "open": float(open_),
                        "high": float(high),
                        "low": float(low),
                        "close": float(close),
                        "volume": float(volume),
                    }
                )
            except Exception as exc:  # defensive parsing
                logger.debug(f"Skipping malformed Binance candle {row}: {exc}")
                continue
        return candles


def create_binance_client(config: Optional[Dict[str, Any]]) -> Optional[BinanceClient]:
    """Factory helper."""
    if not config or not config.get("enabled"):
        return None

    base_url = config.get("base_url", "").strip()
    if not base_url:
        logger.warning("Binance enabled but base_url missing.")
        return None

    return BinanceClient(
        base_url=base_url,
        timeout=config.get("timeout", 10),
        candles_endpoint=config.get("candles_endpoint", "/api/v3/klines"),
        interval_map=config.get("interval_map", {}),
    )

