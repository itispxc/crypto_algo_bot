"""
Simple client for fetching market data from the Horus API.

Horus provides blockchain-aware market data that can be used as a fallback
when the Roostoo mock exchange does not expose historical candles.
"""
from __future__ import annotations

import logging
import os
from typing import List, Dict, Optional, Any

import requests

logger = logging.getLogger(__name__)


class HorusClient:
    """Lightweight wrapper around the Horus REST API."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 10,
        candles_endpoint: str = "/market/candles",
        symbol_param: str = "symbol",
        interval_param: str = "interval",
        limit_param: str = "limit",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.candles_endpoint = candles_endpoint
        self.symbol_param = symbol_param
        self.interval_param = interval_param
        self.limit_param = limit_param
        self.session = requests.Session()

    def _build_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        return headers

    def get_candles(
        self, symbol: str, interval: str = "5m", limit: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Fetch OHLCV candles from Horus.

        Args:
            symbol: Horus market symbol (e.g. BTCUSD).
            interval: Candle interval (5m/15m/1h/etc.).
            limit: Number of candles to request.

        Returns:
            List of dictionaries with at least timestamp/open/high/low/close/volume.
        """
        if not self.base_url or not self.candles_endpoint:
            logger.debug("Horus client not configured with a candles endpoint.")
            return []

        url = f"{self.base_url}{self.candles_endpoint}"
        params = {
            self.symbol_param: symbol,
            self.interval_param: interval,
            self.limit_param: limit,
        }

        try:
            response = self.session.get(
                url, params=params, headers=self._build_headers(), timeout=self.timeout
            )
            response.raise_for_status()
        except Exception as exc:
            logger.warning(f"Horus request failed for {symbol}: {exc}")
            return []

        try:
            payload = response.json()
        except ValueError:
            logger.warning("Failed to decode Horus response as JSON.")
            return []

        if isinstance(payload, dict):
            # Many APIs wrap the candles under a top-level key.
            for key in ("data", "result", "candles", "items", "payload"):
                if key in payload and isinstance(payload[key], list):
                    payload = payload[key]
                    break

        if not isinstance(payload, list):
            logger.warning("Unexpected Horus payload format.")
            return []

        candles: List[Dict[str, Any]] = []
        for row in payload:
            try:
                if isinstance(row, dict):
                    ts = row.get("timestamp") or row.get("time") or row.get("ts") or row.get(
                        "open_time"
                    )
                    open_ = row.get("open") or row.get("o")
                    high = row.get("high") or row.get("h")
                    low = row.get("low") or row.get("l")
                    close = row.get("close") or row.get("c")
                    volume = row.get("volume") or row.get("v")
                elif isinstance(row, (list, tuple)) and len(row) >= 6:
                    ts, open_, high, low, close, volume = row[:6]
                else:
                    logger.debug(f"Skipping unexpected candle item: {row}")
                    continue

                if ts is None:
                    continue
                ts = float(ts)
                if ts < 1e12:  # assume seconds, convert to ms
                    ts = int(ts * 1000)
                else:
                    ts = int(ts)

                candles.append(
                    {
                        "timestamp": ts,
                        "open": float(open_),
                        "high": float(high),
                        "low": float(low),
                        "close": float(close),
                        "volume": float(volume) if volume is not None else 0.0,
                    }
                )
            except Exception as exc:  # defensive parsing
                logger.debug(f"Error parsing Horus candle {row}: {exc}")
                continue

        return candles


def create_horus_client(config: Dict[str, Any]) -> Optional[HorusClient]:
    """Factory helper used by the data client."""
    if not config or not config.get("enabled"):
        return None

    base_url = config.get("base_url", "").strip()
    if not base_url:
        logger.warning("Horus enabled but base_url missing.")
        return None

    api_key = config.get("api_key")
    if not api_key:
        env_var = config.get("api_key_env")
        if env_var:
            api_key = os.getenv(env_var)

    return HorusClient(
        base_url=base_url,
        api_key=api_key,
        timeout=config.get("timeout", 10),
        candles_endpoint=config.get("candles_endpoint", "/market/candles"),
        symbol_param=config.get("symbol_param", "symbol"),
        interval_param=config.get("interval_param", "interval"),
        limit_param=config.get("limit_param", "limit"),
    )

