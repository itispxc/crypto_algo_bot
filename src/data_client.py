"""
Data client for fetching market data and executing trades.
Integrates with Roostoo API.
"""
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

import sys
import os
# Add parent directory to path for roostoo_client and config
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.data_classes import Candle, MarketSnapshot, PortfolioState, Position
from roostoo_client import RoostooClient
from config import Config
from binance_client import create_binance_client

logger = logging.getLogger(__name__)


class DataClient:
    """Client for fetching data and executing trades."""
    
    def __init__(self, config: dict):
        """
        Initialize data client.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.roostoo_config = Config()
        self.client = RoostooClient(
            api_key=self.roostoo_config.ROOSTOO_API_KEY,
            api_secret=self.roostoo_config.ROOSTOO_API_SECRET,
            base_url=self.roostoo_config.ROOSTOO_BASE_URL
        )
        binance_cfg = config.get("binance", {})
        self.binance_client = create_binance_client(binance_cfg)
        self.binance_symbol_map = binance_cfg.get("symbol_map", {}) if binance_cfg else {}
        self.binance_interval_map = binance_cfg.get("interval_map", {}) if binance_cfg else {}
        if self.binance_client:
            logger.info("Binance data source enabled.")
        self.exchange_info = None
        self.pair_filters: Dict[str, Dict[str, float]] = {}
        self._load_exchange_info()
    
    def _load_exchange_info(self):
        """Load exchange information once."""
        try:
            self.exchange_info = self.client.get_exchange_info()
            self.pair_filters = self._extract_pair_filters(self.exchange_info)
        except Exception as e:
            logger.warning(f"Failed to load exchange info: {e}")
            self.exchange_info = {}
            self.pair_filters = {}

    def _extract_pair_filters(self, info: Optional[Dict]) -> Dict[str, Dict[str, float]]:
        """
        Parse exchange info to determine per-pair precision/step sizes.
        """
        filters: Dict[str, Dict[str, float]] = {}
        if not info or not isinstance(info, dict):
            return filters

        candidates = []
        possible_keys = ["Pairs", "pairs", "Data", "data", "Symbols", "symbols", "Result", "result", "TradePairs", "tradePairs"]
        for key in possible_keys:
            if key in info:
                raw = info[key]
                if isinstance(raw, dict):
                    candidates.extend([(k, v) for k, v in raw.items()])
                elif isinstance(raw, list):
                    for entry in raw:
                        if isinstance(entry, dict):
                            pair = entry.get("Pair") or entry.get("symbol") or entry.get("Symbol")
                            candidates.append((pair, entry))
                break

        if not candidates and info.get("Success") and isinstance(info.get("TradingPairs"), list):
            for entry in info.get("TradingPairs", []):
                if isinstance(entry, dict):
                    pair = entry.get("Pair") or entry.get("symbol")
                    candidates.append((pair, entry))
        if not candidates and isinstance(info.get("TradePairs"), dict):
            for pair, entry in info.get("TradePairs").items():
                if isinstance(entry, dict):
                    candidates.append((pair, entry))

        for pair, data in candidates:
            if not pair or not isinstance(data, dict):
                continue

            def _get_float(keys):
                for key in keys:
                    if key in data and data[key] not in (None, ""):
                        try:
                            return float(data[key])
                        except (TypeError, ValueError):
                            continue
                return None

            price_step = _get_float(["PriceStep", "priceStep", "TickSize", "tickSize", "price_step", "priceIncrement"])
            qty_step = _get_float(["QuantityStep", "quantityStep", "QtyStep", "stepSize", "qty_step", "lotSize"])
            min_qty = _get_float(["MinQuantity", "minQuantity", "MinQty", "minQty"])
            min_notional = _get_float(["MinNotional", "minNotional", "MinAmount", "minAmount", "MiniOrder"])
            precision_price = _get_float(["PrecisionPrice", "pricePrecision"])
            precision_qty = _get_float(["PrecisionQty", "quantityPrecision", "AmountPrecision"])

            if not price_step and precision_price is not None:
                price_step = 10 ** (-int(precision_price))
            if not qty_step and precision_qty is not None:
                qty_step = 10 ** (-int(precision_qty))

            filters[pair] = {
                "price_step": price_step or 0.01,
                "qty_step": qty_step or 0.0001,
                "min_qty": min_qty or 0.0,
                "min_notional": min_notional or 0.0,
            }

        return filters if filters else {}

    def get_pair_filters(self, pair: str) -> Dict[str, float]:
        """
        Return precision filters for a pair if available.
        """
        return self.pair_filters.get(pair, {})
    
    def get_candles(self, pair: str, interval: str, limit: int) -> List[Candle]:
        """
        Get candlestick data.
        
        Args:
            pair: Trading pair
            interval: Time interval (5m, 30m, 1h, etc.)
            limit: Number of candles
            
        Returns:
            List of Candle objects
        """
        try:
            candles = self._get_binance_candles(pair, interval, limit)
            if candles:
                return candles

            klines = self.client.get_klines(pair, interval=interval, limit=limit)
            if not klines:
                # Fallback: create synthetic candles from ticker
                logger.warning(f"No klines for {pair}, using ticker data")
                snapshot = self.get_snapshot(pair)
                if snapshot:
                    # Create a single candle from snapshot
                    price = snapshot.price
                    return [Candle(
                        ts=int(time.time() * 1000),
                        open=price,
                        high=price * 1.001,
                        low=price * 0.999,
                        close=price,
                        volume=snapshot.vol24h / 24 / 60  # Approximate
                    )]
                return []
            
            candles = []
            for k in klines:
                # Handle different kline formats
                if isinstance(k, list) and len(k) >= 6:
                    # [timestamp, open, high, low, close, volume, ...]
                    candles.append(Candle(
                        ts=int(k[0]),
                        open=float(k[1]),
                        high=float(k[2]),
                        low=float(k[3]),
                        close=float(k[4]),
                        volume=float(k[5])
                    ))
                elif isinstance(k, dict):
                    # Dict format
                    candles.append(Candle(
                        ts=int(k.get('timestamp', k.get('ts', time.time() * 1000))),
                        open=float(k.get('open', k.get('o', 0))),
                        high=float(k.get('high', k.get('h', 0))),
                        low=float(k.get('low', k.get('l', 0))),
                        close=float(k.get('close', k.get('c', k.get('price', 0)))),
                        volume=float(k.get('volume', k.get('v', 0)))
                    ))
            
            return candles
            
        except Exception as e:
            logger.error(f"Failed to get candles for {pair}: {e}")
            # Fallback to ticker
            try:
                snapshot = self.get_snapshot(pair)
                if snapshot:
                    price = snapshot.price
                    return [Candle(
                        ts=int(time.time() * 1000),
                        open=price,
                        high=price * 1.001,
                        low=price * 0.999,
                        close=price,
                        volume=snapshot.vol24h / 24 / 60
                    )]
            except:
                pass
            return []

    def _map_binance_symbol(self, pair: str) -> Optional[str]:
        """
        Map a Roostoo pair into the Binance symbol space.
        """
        if pair in self.binance_symbol_map:
            return self.binance_symbol_map[pair]
        return pair.replace("/", "") if pair else None

    def _get_binance_candles(self, pair: str, interval: str, limit: int) -> List[Candle]:
        """
        Try to fetch candles from Binance if configured.
        """
        if not self.binance_client:
            return []

        symbol = self._map_binance_symbol(pair)
        if not symbol:
            return []

        raw_candles = self.binance_client.get_candles(symbol, interval=interval, limit=limit)
        candles: List[Candle] = []
        for item in raw_candles:
            try:
                ts = int(item["timestamp"])
                if ts < 1e12:
                    ts *= 1000
                candles.append(Candle(
                    ts=ts,
                    open=float(item["open"]),
                    high=float(item["high"]),
                    low=float(item["low"]),
                    close=float(item["close"]),
                    volume=float(item.get("volume", 0.0))
                ))
            except Exception as exc:
                logger.debug(f"Skipping malformed Binance candle for {pair}: {exc}")
                continue
        return candles
    
    def get_snapshot(self, pair: str) -> Optional[MarketSnapshot]:
        """
        Get market snapshot for a pair.
        
        Args:
            pair: Trading pair
            
        Returns:
            MarketSnapshot or None
        """
        try:
            ticker = self.client.get_ticker(pair)
            
            if ticker.get('Success') and 'Data' in ticker:
                data = ticker['Data'].get(pair, {})
                return MarketSnapshot(
                    pair=pair,
                    price=float(data.get('LastPrice', 0)),
                    bid=float(data.get('MaxBid', 0)),
                    ask=float(data.get('MinAsk', 0)),
                    vol24h=float(data.get('CoinTradeValue', 0))
                )
            return None
            
        except Exception as e:
            logger.error(f"Failed to get snapshot for {pair}: {e}")
            return None
    
    def get_all_snapshots(self, pairs: List[str]) -> Dict[str, MarketSnapshot]:
        """
        Get market snapshots for multiple pairs.
        
        Args:
            pairs: List of trading pairs
            
        Returns:
            Dictionary mapping pair to MarketSnapshot
        """
        snapshots = {}
        for pair in pairs:
            snapshot = self.get_snapshot(pair)
            if snapshot:
                snapshots[pair] = snapshot
            # Rate limiting
            time.sleep(self.config['exchange']['rate_limit_ms'] / 1000.0)
        return snapshots
    
    def get_positions(self) -> PortfolioState:
        """
        Get current portfolio state.
        
        Returns:
            PortfolioState
        """
        try:
            balance = self.client.get_balance()
            
            if not balance.get('Success'):
                logger.error("Failed to get balance")
                return self._empty_state()
            
            spot_wallet = balance.get('SpotWallet', {})
            usd_balance = spot_wallet.get('USD', {})
            cash_usd = float(usd_balance.get('Free', 0))
            
            # Get positions from orders
            positions = {}
            orders = self.client.query_order(limit=100)
            
            if orders.get('Success'):
                order_list = orders.get('OrderMatched', [])
                for order in order_list:
                    if order.get('Status') == 'FILLED' and order.get('Side') == 'BUY':
                        pair = order.get('Pair')
                        qty = float(order.get('FilledQuantity', 0))
                        price = float(order.get('FilledAverPrice', 0))
                        
                        if qty > 0 and pair:
                            if pair not in positions:
                                positions[pair] = Position(
                                    pair=pair,
                                    quantity=qty,
                                    avg_price=price,
                                    usd_value=qty * price
                                )
                            else:
                                # Update existing position
                                pos = positions[pair]
                                total_qty = pos.quantity + qty
                                total_cost = pos.avg_price * pos.quantity + price * qty
                                pos.avg_price = total_cost / total_qty if total_qty > 0 else price
                                pos.quantity = total_qty
                                pos.usd_value = total_qty * price
            
            # Calculate equity
            equity = cash_usd
            for pos in positions.values():
                snapshot = self.get_snapshot(pos.pair)
                if snapshot:
                    pos.usd_value = pos.quantity * snapshot.price
                    equity += pos.usd_value
            
            return PortfolioState(
                cash_usd=cash_usd,
                positions=positions,
                equity=equity,
                peak_equity=equity,
            last_rebalance_ts=int(time.time() * 1000),
            fast_start_active=False,
            fast_start_completed=False,
            fast_start_entry_price=None,
            fast_start_target_price=None
            )
            
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return self._empty_state()
    
    def _empty_state(self) -> PortfolioState:
        """Return empty portfolio state."""
        return PortfolioState(
            cash_usd=0.0,
            positions={},
            equity=0.0,
            peak_equity=0.0,
            last_rebalance_ts=int(time.time() * 1000),
            fast_start_active=False,
            fast_start_completed=False,
            fast_start_entry_price=None,
            fast_start_target_price=None
        )
    
    def place_order(self, pair: str, side: str, qty: float, 
                   price: Optional[float] = None, order_type: str = "limit") -> Optional[str]:
        """
        Place an order.
        
        Args:
            pair: Trading pair
            side: 'buy' or 'sell'
            qty: Quantity
            price: Price for limit orders
            order_type: 'limit' or 'market'
            
        Returns:
            Order ID or None
        """
        try:
            if self.config['ops']['dry_run']:
                logger.info(f"[DRY RUN] Would place {order_type} {side} order: {qty} {pair} @ {price}")
                return f"dry_run_{int(time.time())}"
            
            order = self.client.place_order(
                pair=pair,
                side=side.upper(),
                quantity=qty,
                price=price
            )
            
            if order.get('Success'):
                order_detail = order.get('OrderDetail', {})
                order_id = order_detail.get('OrderID')
                logger.info(f"Order placed: {order_id} - {side} {qty} {pair}")
                return str(order_id) if order_id else None
            
            logger.error(f"Order failed: {order.get('ErrMsg', 'Unknown error')}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return None
    
    def get_order_status(self, order_id: str) -> Optional[dict]:
        """
        Get order status.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order status dict or None
        """
        try:
            orders = self.client.query_order(order_id=order_id)
            if orders.get('Success'):
                order_list = orders.get('OrderMatched', [])
                if order_list:
                    return order_list[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID
            
        Returns:
            True if cancelled successfully
        """
        try:
            if self.config['ops']['dry_run']:
                logger.info(f"[DRY RUN] Would cancel order: {order_id}")
                return True
            
            result = self.client.cancel_order(order_id=order_id)
            return result.get('Success', False)
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False

