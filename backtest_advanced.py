"""
Advanced backtesting system with TradingView-style visualization.
Shows profit charts, performance metrics, and trade history.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import json
import os

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_classes import Candle, Signal
from src.feature_engine import compute_features
from src.regime import compute_market_regime
from src.alpha_model import load_models, score_signals
from src.portfolio import build_target_weights
from src.utils import ema, infer_tier
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedBacktester:
    """Advanced backtesting engine with visualization."""
    
    def __init__(self, initial_balance: float = 50000.0, config_path: str = "config/config.yaml", random_seed: int = 42):
        """
        Initialize backtester.
        
        Args:
            initial_balance: Starting balance
            config_path: Path to config file
            random_seed: Random seed for reproducible results (default: 42)
        """
        # Set global random seed for reproducibility
        np.random.seed(random_seed)
        self.random_seed = random_seed
        
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.cash = initial_balance
        self.positions = {}  # {pair: {'qty': float, 'entry_price': float, 'entry_time': datetime}}
        self.trades = []
        self.equity_curve = []
        self.trade_history = []
        self.daily_returns = []
        
        # Load config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Load models (if available)
        try:
            self.models = load_models(self.config)
        except:
            self.models = {"6h": None, "24h": None}
    
    def load_historical_data(self, pair: str, start_date: datetime, 
                            end_date: datetime, interval: str = '5m') -> pd.DataFrame:
        """
        Load historical data for backtesting.
        
        For now, generates synthetic data. In production, you'd fetch from:
        - Horus data source
        - Exchange historical data API
        - Downloaded CSV files
        
        Args:
            pair: Trading pair
            start_date: Start date
            end_date: End date
            interval: Data interval
            
        Returns:
            DataFrame with OHLCV data
        """
        logger.info(f"Loading historical data for {pair} from {start_date} to {end_date}")
        
        # Generate synthetic data for demonstration
        # In production, replace with actual data fetching
        periods = int((end_date - start_date).total_seconds() / (5 * 60))  # 5-minute intervals
        
        # Ensure we have enough data for features (need at least 600 candles = 50 hours)
        if periods < 600:
            periods = 600
            start_date = end_date - timedelta(hours=50)
        
        timestamps = pd.date_range(start=start_date, periods=periods, freq='5min')
        
        # Generate realistic price movements with trends
        # Use consistent seed based on pair name + global seed for reproducibility
        # This ensures same pair+period always gets same data, but different periods get different data
        # Include period dates in hash so different periods generate different price movements
        period_key = (pair, start_date.date(), end_date.date())
        period_hash = hash(period_key)
        pair_hash = (period_hash + self.random_seed) % (2**31)  # Combine with global seed
        np.random.seed(pair_hash)
        initial_price = 50000.0 if 'BTC' in pair else 3000.0 if 'ETH' in pair else 100.0
        
        # Generate realistic returns (small per-period returns)
        # Each 5-minute period should have small returns, not large ones
        # Annual volatility ~50% = daily ~3% = 5min ~0.1%
        daily_vol = 0.03  # 3% daily volatility
        period_vol = daily_vol / np.sqrt(288)  # 288 5-min periods per day
        
        # Add small upward trend (0.02% per period = ~5% per day max)
        trend_per_period = 0.0002  # 0.02% per 5-min period
        noise = np.random.normal(0, period_vol, periods)
        returns = trend_per_period + noise
        
        # Generate prices with geometric random walk
        prices = [initial_price]
        for ret in returns:
            # Clamp returns to reasonable bounds (-5% to +5% per period)
            ret = np.clip(ret, -0.05, 0.05)
            prices.append(prices[-1] * (1 + ret))
        prices = prices[1:]
        
        # Ensure prices stay in reasonable range
        prices = np.array(prices)
        prices = np.clip(prices, initial_price * 0.5, initial_price * 2.0)  # Stay within 50%-200% of initial
        
        # Create OHLCV with proper structure
        data = []
        for i, (ts, price) in enumerate(zip(timestamps, prices)):
            if i == 0:
                open_price = initial_price
            else:
                open_price = prices[i-1]
            
            # Create realistic OHLC
            volatility = abs(np.random.normal(0, 0.003))
            high = price * (1 + volatility)
            low = price * (1 - volatility)
            # Ensure high >= close >= low
            high = max(high, price)
            low = min(low, price)
            
            volume = np.random.uniform(100, 1000)
            
            data.append({
                'timestamp': ts,
                'open': open_price,
                'high': high,
                'low': low,
                'close': price,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        logger.info(f"Generated {len(df)} candles for {pair}")
        return df
    
    def load_data_from_csv(self, file_path: str) -> pd.DataFrame:
        """
        Load historical data from CSV file.
        
        Expected format: timestamp,open,high,low,close,volume
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            df = pd.read_csv(file_path)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            return pd.DataFrame()
    
    def run_backtest(self, data: Dict[str, pd.DataFrame], 
                    start_date: datetime, end_date: datetime) -> Dict:
        """
        Run backtest on historical data.
        
        Args:
            data: Dictionary mapping pair to DataFrame
            start_date: Start date
            end_date: End date
            
        Returns:
            Backtest results dictionary
        """
        logger.info("=" * 60)
        logger.info("Starting Advanced Backtest")
        logger.info(f"Period: {start_date.date()} to {end_date.date()}")
        logger.info(f"Initial Balance: ${self.initial_balance:,.2f}")
        logger.info("=" * 60)
        
        # Get all pairs
        pairs = list(data.keys())
        if not pairs:
            logger.error("No data provided")
            return {}
        
        # Resample to 30-minute bars for feature computation
        data_30m = {}
        for pair, df in data.items():
            if len(df) > 0:
                resampled = df.resample('30min').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
                data_30m[pair] = resampled
        
        # Main backtest loop (process every 30 minutes)
        # Start at a deterministic time (round to nearest 30 minutes)
        start_minute = start_date.minute
        if start_minute < 15:
            current_time = start_date.replace(minute=0, second=0, microsecond=0)
        elif start_minute < 45:
            current_time = start_date.replace(minute=30, second=0, microsecond=0)
        else:
            current_time = (start_date + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        
        last_rebalance = None
        rebalance_count = 0
        total_iterations = 0
        
        logger.info(f"Starting backtest loop from {current_time} to {end_date}")
        logger.info(f"Will process approximately {int((end_date - current_time).total_seconds() / 1800)} 30-minute intervals")
        
        while current_time < end_date:
            total_iterations += 1
            try:
                # Get current snapshots (current price for each pair)
                snapshots = {}
                for pair in pairs:
                    if pair in data and len(data[pair]) > 0:
                        # Find closest timestamp
                        df = data[pair]
                        if current_time in df.index:
                            row = df.loc[current_time]
                        else:
                            # Find closest
                            closest_idx = df.index.get_indexer([current_time], method='nearest')[0]
                            row = df.iloc[closest_idx]
                        
                        snapshots[pair] = {
                            'price': float(row['close']),
                            'timestamp': row.name if hasattr(row, 'name') else current_time
                        }
                
                # Mark to market
                equity = self.cash
                for pair, pos in self.positions.items():
                    if pair in snapshots:
                        price = snapshots[pair]['price']
                        equity += pos['qty'] * price
                
                # Record equity curve
                self.equity_curve.append({
                    'timestamp': current_time,
                    'equity': equity,
                    'cash': self.cash,
                    'positions_value': equity - self.cash
                })
                
                # Rebalance logic (every 30 minutes or at scheduled times)
                # Use deterministic timing based on minutes since start
                minutes_since_start = (current_time - start_date).total_seconds() / 60
                
                should_rebalance = False
                
                # Force first rebalance after enough data is collected (50 hours = 3000 minutes)
                if last_rebalance is None:
                    if minutes_since_start >= 3000:
                        # Rebalance at the first 30-minute mark after 3000 minutes
                        if current_time.minute in [0, 30]:
                            should_rebalance = True
                            logger.info(f"First rebalance triggered at {current_time} (after {minutes_since_start:.0f} minutes)")
                else:
                    # Regular rebalancing every 30 minutes
                    if current_time.minute in [0, 30]:
                        should_rebalance = True
                    # Also rebalance at scheduled times
                    if current_time.strftime("%H:%M") in ["00:00", "06:00", "12:00", "18:00"]:
                        should_rebalance = True
                
                if should_rebalance and (last_rebalance is None or 
                    (current_time - last_rebalance).total_seconds() >= 1800):
                    
                    logger.debug(f"Rebalancing check at {current_time}, last_rebalance={last_rebalance}")
                    
                    # Get candles for feature computation
                    candles_5m = {}
                    candles_30m = {}
                    
                    lookback = timedelta(days=5)
                    for pair in pairs:
                        if pair in data:
                            df_5m = data[pair]
                            df_30m = data_30m.get(pair, pd.DataFrame())
                            
                            # Get recent data
                            mask_5m = (df_5m.index >= current_time - lookback) & (df_5m.index <= current_time)
                            mask_30m = (df_30m.index >= current_time - lookback) & (df_30m.index <= current_time)
                            
                            recent_5m = df_5m[mask_5m].tail(600)
                            recent_30m = df_30m[mask_30m].tail(200)
                            
                            if len(recent_5m) > 0:
                                candles_5m[pair] = [
                                    Candle(
                                        ts=int(ts.timestamp() * 1000),
                                        open=float(row['open']),
                                        high=float(row['high']),
                                        low=float(row['low']),
                                        close=float(row['close']),
                                        volume=float(row['volume'])
                                    )
                                    for ts, row in recent_5m.iterrows()
                                ]
                            
                            if len(recent_30m) > 0:
                                candles_30m[pair] = [
                                    Candle(
                                        ts=int(ts.timestamp() * 1000),
                                        open=float(row['open']),
                                        high=float(row['high']),
                                        low=float(row['low']),
                                        close=float(row['close']),
                                        volume=float(row['volume'])
                                    )
                                    for ts, row in recent_30m.iterrows()
                                ]
                    
                    # Compute features and signals
                    if candles_5m and candles_30m:
                        # Check if we have enough data
                        min_candles_5m = min(len(c) for c in candles_5m.values()) if candles_5m else 0
                        min_candles_30m = min(len(c) for c in candles_30m.values()) if candles_30m else 0
                        
                        if min_candles_5m < 288 or min_candles_30m < 48:
                            logger.warning(f"Insufficient data: 5m={min_candles_5m}, 30m={min_candles_30m}")
                            current_time += timedelta(minutes=30)
                            continue
                        
                        features = compute_features(candles_5m, candles_30m, self.config)
                        logger.debug(f"Computed features for {len(features)} pairs")
                        
                        # Compute regime
                        btc_candles = candles_30m.get('BTC/USD', [])
                        if btc_candles:
                            regime_info = compute_market_regime(btc_candles)
                        else:
                            regime_info = {"regime": "trend", "vol_regime": "mid", "breadth": 0.6}  # Default to trend for more signals
                        
                        # Score signals
                        signals = score_signals(self.models, features, regime_info, self.config)
                        logger.debug(f"Generated {len(signals)} signals")
                        
                        if not signals:
                            logger.warning("No signals generated")
                            current_time += timedelta(minutes=30)
                            continue
                        
                        # Build target weights
                        from src.portfolio import PortfolioState
                        state = PortfolioState(
                            cash_usd=self.cash,
                            positions={},
                            equity=equity,
                            peak_equity=max(equity, self.initial_balance),
                            last_rebalance_ts=int(current_time.timestamp() * 1000)
                        )
                        
                        # Use consistent threshold for reproducibility
                        # Always use a fixed threshold for backtesting to ensure consistency
                        score_threshold = self.config["signals"]["score_threshold"]
                        passing_signals = [s for s in signals.values() if s.exp_ret_net > score_threshold]
                        
                        # Log signal values for debugging
                        if signals:
                            logger.info(f"Signal values: {[(p, round(s.exp_ret_net, 6), round(s.score, 6)) for p, s in list(signals.items())[:3]]}")
                        
                        # For backtesting, respect the configured threshold
                        # Only use fallback if explicitly needed (for initial data collection)
                        # During optimization, we want to see the real effect of different thresholds
                        if not passing_signals and len(signals) > 0:
                            # Only use fallback if we're in the initial warmup period
                            # Otherwise, respect the threshold - this allows optimization to work properly
                            if len(self.equity_curve) < 10:  # Very early in backtest
                                logger.info(f"No signals pass threshold {score_threshold}, using fallback threshold 0.001 (warmup)")
                                temp_config = self.config.copy()
                                temp_config["signals"]["score_threshold"] = 0.001
                                target_weights = build_target_weights(signals, regime_info, state, temp_config)
                            else:
                                # After warmup, respect the actual threshold for optimization
                                logger.debug(f"No signals pass threshold {score_threshold}, skipping rebalance")
                                target_weights = {}
                        else:
                            target_weights = build_target_weights(signals, regime_info, state, self.config)
                        
                        logger.debug(f"Built {len(target_weights)} target weights")
                        
                        # Execute rebalancing
                        if target_weights:
                            rebalance_count += 1
                            logger.info(f"Rebalancing #{rebalance_count} at {current_time}: {len(target_weights)} target positions")
                            trades_before = len(self.trade_history)
                            self._rebalance(target_weights, snapshots, current_time)
                            trades_after = len(self.trade_history)
                            new_trades = trades_after - trades_before
                            logger.info(f"Rebalanced: {new_trades} new trades, {len(self.positions)} positions, cash=${self.cash:.2f}")
                        else:
                            logger.warning(f"No target weights at {current_time} - signals may not meet threshold")
                        
                        last_rebalance = current_time
                
                # Advance time
                current_time += timedelta(minutes=30)
                
                # Progress indicator for long backtests
                if int((current_time - start_date).total_seconds()) % 86400 == 0:  # Every day
                    progress = ((current_time - start_date).total_seconds() / (end_date - start_date).total_seconds()) * 100
                    logger.info(f"Backtest progress: {progress:.1f}% ({current_time.date()})")
                
            except Exception as e:
                logger.error(f"Error at {current_time}: {e}", exc_info=True)
                current_time += timedelta(minutes=30)
                continue
        
        logger.info(f"Backtest loop completed: {total_iterations} iterations, {rebalance_count} rebalances")
        logger.info(f"Final positions: {len(self.positions)}, Total trades: {len(self.trade_history)}")
        
        # Close all positions at end
        final_snapshots = {}
        for pair in self.positions.keys():
            if pair in data and len(data[pair]) > 0:
                final_row = data[pair].iloc[-1]
                final_snapshots[pair] = {'price': float(final_row['close'])}
        
        if self.positions:
            logger.info(f"Closing {len(self.positions)} positions at end of backtest")
        # Get fee rate for closing positions
        fee_bps = self.config.get("exchange", {}).get("fee_bps", 10)
        fee_rate = fee_bps / 10000.0
        self._close_all_positions(final_snapshots, end_date, fee_rate)
        
        # Calculate results
        logger.info(f"Calculating results: {len(self.equity_curve)} equity points, {len(self.trade_history)} trades")
        return self._calculate_results()
    
    def _rebalance(self, target_weights: Dict[str, float], 
                  snapshots: Dict, current_time: datetime):
        """Execute rebalancing."""
        equity = self.cash
        for pair, pos in self.positions.items():
            if pair in snapshots:
                equity += pos['qty'] * snapshots[pair]['price']
        
        logger.debug(f"Rebalancing: equity=${equity:.2f}, {len(target_weights)} target weights")
        
        for pair, target_w in target_weights.items():
            if pair not in snapshots:
                logger.debug(f"Skipping {pair}: no snapshot")
                continue
            
            price = snapshots[pair]['price']
            current_pos = self.positions.get(pair, {'qty': 0, 'entry_price': 0, 'entry_time': None})
            current_qty = current_pos['qty']
            current_value = current_qty * price
            current_w = current_value / max(equity, 1e-6)
            
            # Check hysteresis - skip if weight change is too small
            hyster = self.config.get("signals", {}).get("hysteresis_weight_change", 0.03)
            if abs(target_w - current_w) < hyster:
                logger.debug(f"Skipping {pair}: weight change {abs(target_w - current_w):.4f} < hysteresis {hyster:.4f}")
                continue
            
            target_value = target_w * equity
            target_qty = target_value / price
            
            delta_qty = target_qty - current_qty
            
            # Execute trade
            min_order_usd = self.config.get("exchange", {}).get("min_order_usd", 100.0)
            delta_usd = abs(delta_qty * price)
            
            if abs(delta_qty) > 1e-6 and delta_usd >= min_order_usd:
                # Get fee rate from config
                fee_bps = self.config.get("exchange", {}).get("fee_bps", 10)
                fee_rate = fee_bps / 10000.0  # Convert basis points to decimal
                
                logger.debug(f"{pair}: current_w={current_w:.4f}, target_w={target_w:.4f}, delta_qty={delta_qty:.6f}, delta_usd=${delta_usd:.2f}")
                if delta_qty > 0:  # Buy
                    cost = delta_qty * price
                    fee = cost * fee_rate  # Fee on buy
                    total_cost = cost + fee
                    
                    if total_cost <= self.cash:
                        self.cash -= total_cost  # Deduct cost + fee
                        if pair not in self.positions:
                            self.positions[pair] = {'qty': 0, 'entry_price': 0, 'entry_time': None}
                        
                        # Update position (weighted average)
                        old_qty = self.positions[pair]['qty']
                        old_price = self.positions[pair]['entry_price']
                        new_qty = old_qty + delta_qty
                        if new_qty > 0:
                            if old_qty > 0:
                                new_price = (old_qty * old_price + delta_qty * price) / new_qty
                            else:
                                new_price = price
                            self.positions[pair]['qty'] = new_qty
                            self.positions[pair]['entry_price'] = new_price
                            self.positions[pair]['entry_time'] = current_time
                            
                            logger.info(f"BUY {delta_qty:.6f} {pair} @ ${price:.2f}, cost=${cost:.2f}, fee=${fee:.2f}, total=${total_cost:.2f}")
                            self._record_trade('BUY', pair, delta_qty, price, current_time, fee=fee)
                    else:
                        logger.warning(f"Insufficient cash for {pair}: need ${total_cost:.2f} (cost ${cost:.2f} + fee ${fee:.2f}), have ${self.cash:.2f}")
                
                else:  # Sell
                    sell_qty = abs(delta_qty)
                    if sell_qty <= current_qty + 1e-6:  # Allow small rounding errors
                        revenue = sell_qty * price
                        fee = revenue * fee_rate  # Fee on sell
                        net_revenue = revenue - fee
                        self.cash += net_revenue  # Add revenue minus fee
                        self.positions[pair]['qty'] -= sell_qty
                        
                        if self.positions[pair]['qty'] <= 1e-6:
                            # Calculate P&L for closed position (accounting for fees)
                            entry_price = current_pos['entry_price']
                            # Profit = (sell_price - entry_price) * qty - fees
                            profit = (price - entry_price) * sell_qty - fee
                            logger.info(f"SELL {sell_qty:.6f} {pair} @ ${price:.2f}, revenue=${revenue:.2f}, fee=${fee:.2f}, net=${net_revenue:.2f}, profit=${profit:.2f}")
                            self._record_trade('SELL', pair, sell_qty, price, current_time, 
                                             entry_price, profit, fee=fee)
                            del self.positions[pair]
                        else:
                            logger.info(f"SELL {sell_qty:.6f} {pair} @ ${price:.2f}, revenue=${revenue:.2f}, fee=${fee:.2f} (partial)")
                            self._record_trade('SELL', pair, sell_qty, price, current_time, fee=fee)
                    else:
                        logger.warning(f"Cannot sell {sell_qty:.6f} {pair}, only have {current_qty:.6f}")
            elif abs(delta_qty) > 1e-6:
                logger.debug(f"Skipping {pair}: delta_usd=${delta_usd:.2f} < min_order=${min_order_usd:.2f}")
    
    def _record_trade(self, action: str, pair: str, qty: float, price: float,
                     timestamp: datetime, entry_price: float = None, profit: float = None, fee: float = 0.0):
        """Record a trade."""
        trade = {
            'timestamp': timestamp,
            'action': action,
            'pair': pair,
            'quantity': qty,
            'price': price,
            'entry_price': entry_price,
            'profit': profit,
            'fee': fee,
            'pnl_pct': (profit / (entry_price * qty) * 100) if entry_price and profit and entry_price > 0 else None
        }
        self.trade_history.append(trade)
    
    def _close_all_positions(self, snapshots: Dict, end_time: datetime, fee_rate: float = 0.001):
        """Close all positions at end of backtest."""
        for pair, pos in list(self.positions.items()):
            if pair in snapshots:
                price = snapshots[pair]['price']
                qty = pos['qty']
                entry_price = pos['entry_price']
                revenue = qty * price
                fee = revenue * fee_rate  # Fee on sell
                net_revenue = revenue - fee
                self.cash += net_revenue  # Add revenue minus fee
                profit = (price - entry_price) * qty - fee  # Profit after fees
                self._record_trade('SELL', pair, qty, price, end_time, entry_price, profit, fee=fee)
                del self.positions[pair]
    
    def _calculate_results(self) -> Dict:
        """Calculate comprehensive backtest results."""
        if not self.equity_curve:
            return {}
        
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df.set_index('timestamp', inplace=True)
        
        # Calculate returns
        equity_values = equity_df['equity'].values
        returns = np.diff(equity_values) / equity_values[:-1]
        returns = returns[~np.isnan(returns)]
        
        # Performance metrics
        total_return = (equity_values[-1] - equity_values[0]) / equity_values[0]
        total_return_pct = total_return * 100
        
        # Sharpe ratio (annualized)
        # Use daily returns instead of 30-min to avoid inflation from many zero-return periods
        # Resample equity curve to daily
        equity_daily = equity_df.resample('D').last()
        if len(equity_daily) > 1:
            equity_daily_values = equity_daily['equity'].values
            daily_returns = np.diff(equity_daily_values) / equity_daily_values[:-1]
            daily_returns = daily_returns[~np.isnan(daily_returns)]
            if len(daily_returns) > 0 and np.std(daily_returns) > 0:
                sharpe = (np.mean(daily_returns) / np.std(daily_returns)) * np.sqrt(252)  # Daily bars, annualized
            else:
                # Fallback to 30-min if daily doesn't work
                if len(returns) > 0 and np.std(returns) > 0:
                    sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252 * 48)
                else:
                    sharpe = 0.0
        else:
            # Fallback to 30-min if we don't have enough daily data
            if len(returns) > 0 and np.std(returns) > 0:
                sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252 * 48)  # 30-min bars
            else:
                sharpe = 0.0
        
        # Sortino ratio (use daily returns for consistency)
        if len(equity_daily) > 1 and len(daily_returns) > 0:
            negative_daily_returns = daily_returns[daily_returns < 0]
            if len(negative_daily_returns) > 0 and np.std(negative_daily_returns) > 0:
                sortino = (np.mean(daily_returns) / np.std(negative_daily_returns)) * np.sqrt(252)
            else:
                sortino = 0.0
        else:
            # Fallback to 30-min
            negative_returns = returns[returns < 0]
            if len(negative_returns) > 0 and np.std(negative_returns) > 0:
                sortino = (np.mean(returns) / np.std(negative_returns)) * np.sqrt(252 * 48)
            else:
                sortino = 0.0
        
        # Maximum drawdown
        running_max = np.maximum.accumulate(equity_values)
        drawdowns = (equity_values - running_max) / running_max
        mdd = float(np.min(drawdowns))
        
        # Calmar ratio (use daily returns for consistency)
        if len(equity_daily) > 1 and len(daily_returns) > 0:
            calmar = (np.mean(daily_returns) * 252) / abs(mdd) if mdd != 0 else 0.0
        else:
            calmar = (np.mean(returns) * 252 * 48) / abs(mdd) if mdd != 0 else 0.0
        
        # Win rate (only count SELL trades with profit recorded)
        profitable_trades = [t for t in self.trade_history if t.get('profit') is not None and t.get('profit', 0) > 0]
        sell_trades = [t for t in self.trade_history if t.get('action') == 'SELL' and t.get('profit') is not None]
        win_rate = (len(profitable_trades) / len(sell_trades) * 100) if sell_trades else 0
        
        # Average profit/loss (only for trades with profit recorded)
        profits = [t.get('profit') for t in self.trade_history if t.get('profit') is not None]
        avg_profit = np.mean(profits) if profits else 0.0
        
        # Total fees paid
        total_fees = sum(t.get('fee', 0) for t in self.trade_history)
        
        # Total trades
        total_trades = len([t for t in self.trade_history if t['action'] == 'SELL'])
        
        return {
            'initial_balance': self.initial_balance,
            'final_balance': equity_values[-1],
            'total_return': equity_values[-1] - self.initial_balance,
            'total_return_pct': total_return_pct,
            'sharpe_ratio': float(sharpe),
            'sortino_ratio': float(sortino),
            'calmar_ratio': float(calmar),
            'max_drawdown': float(mdd),
            'max_drawdown_pct': float(mdd * 100),
            'win_rate': float(win_rate),
            'total_trades': total_trades,
            'avg_profit_per_trade': float(avg_profit),
            'total_fees': float(total_fees),
            'equity_curve': equity_df,
            'trades': self.trade_history
        }
    
    def plot_results(self, results: Dict, data: Dict[str, pd.DataFrame], 
                    pair_to_plot: str = 'BTC/USD', save_path: str = 'backtest_results.png'):
        """
        Create TradingView-style visualization.
        
        Args:
            results: Backtest results
            data: Historical price data
            pair_to_plot: Which pair to show on price chart
            save_path: Where to save the plot
        """
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(4, 2, hspace=0.3, wspace=0.3)
        
        equity_df = results['equity_curve']
        
        # 1. Equity Curve (Top, full width)
        ax1 = fig.add_subplot(gs[0, :])
        ax1.plot(equity_df.index, equity_df['equity'], linewidth=2, color='#2E7D32', label='Equity')
        ax1.axhline(y=self.initial_balance, color='gray', linestyle='--', alpha=0.5, label='Initial Balance')
        ax1.fill_between(equity_df.index, self.initial_balance, equity_df['equity'], 
                         where=(equity_df['equity'] >= self.initial_balance), 
                         alpha=0.3, color='green', label='Profit')
        ax1.fill_between(equity_df.index, self.initial_balance, equity_df['equity'], 
                         where=(equity_df['equity'] < self.initial_balance), 
                         alpha=0.3, color='red', label='Loss')
        ax1.set_title('Portfolio Equity Curve', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Equity ($)', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # 2. Price Chart with Trades (Left)
        ax2 = fig.add_subplot(gs[1, 0])
        if pair_to_plot in data:
            price_df = data[pair_to_plot]
            ax2.plot(price_df.index, price_df['close'], linewidth=1.5, color='#1976D2', label='Price')
            
            # Mark buy/sell trades
            buy_trades = [t for t in self.trade_history if t['pair'] == pair_to_plot and t['action'] == 'BUY']
            sell_trades = [t for t in self.trade_history if t['pair'] == pair_to_plot and t['action'] == 'SELL']
            
            for trade in buy_trades:
                ax2.scatter(trade['timestamp'], trade['price'], color='green', marker='^', 
                           s=100, zorder=5, label='Buy' if trade == buy_trades[0] else '')
            
            for trade in sell_trades:
                ax2.scatter(trade['timestamp'], trade['price'], color='red', marker='v', 
                           s=100, zorder=5, label='Sell' if trade == sell_trades[0] else '')
            
            ax2.set_title(f'{pair_to_plot} Price Chart with Trades', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Price ($)', fontsize=10)
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        # 3. Drawdown Chart (Right)
        ax3 = fig.add_subplot(gs[1, 1])
        equity_values = equity_df['equity'].values
        running_max = np.maximum.accumulate(equity_values)
        drawdowns = (equity_values - running_max) / running_max * 100
        ax3.fill_between(equity_df.index, 0, drawdowns, alpha=0.5, color='red')
        ax3.plot(equity_df.index, drawdowns, linewidth=1.5, color='darkred')
        ax3.set_title('Drawdown (%)', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Drawdown %', fontsize=10)
        ax3.grid(True, alpha=0.3)
        ax3.invert_yaxis()
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
        
        # 4. Returns Distribution (Bottom Left)
        ax4 = fig.add_subplot(gs[2, 0])
        returns = np.diff(equity_values) / equity_values[:-1] * 100
        returns = returns[~np.isnan(returns)]
        ax4.hist(returns, bins=50, alpha=0.7, color='#42A5F5', edgecolor='black')
        ax4.axvline(x=0, color='red', linestyle='--', linewidth=2)
        ax4.set_title('Return Distribution', fontsize=12, fontweight='bold')
        ax4.set_xlabel('Return %', fontsize=10)
        ax4.set_ylabel('Frequency', fontsize=10)
        ax4.grid(True, alpha=0.3)
        
        # 5. Trade P&L (Bottom Right)
        ax5 = fig.add_subplot(gs[2, 1])
        trade_pnl = [t.get('profit', 0) for t in self.trade_history if t.get('profit') is not None]
        if trade_pnl:
            colors = ['green' if p > 0 else 'red' for p in trade_pnl]
            ax5.bar(range(len(trade_pnl)), trade_pnl, color=colors, alpha=0.7)
            ax5.axhline(y=0, color='black', linestyle='-', linewidth=1)
            ax5.set_title('Trade P&L', fontsize=12, fontweight='bold')
            ax5.set_xlabel('Trade Number', fontsize=10)
            ax5.set_ylabel('Profit/Loss ($)', fontsize=10)
            ax5.grid(True, alpha=0.3)
        
        # 6. Performance Metrics Table (Bottom)
        ax6 = fig.add_subplot(gs[3, :])
        ax6.axis('off')
        
        total_fees = results.get('total_fees', 0.0)
        metrics_text = f"""
        PERFORMANCE METRICS
        {'='*80}
        
        Returns:
          Total Return:          ${results['total_return']:,.2f} ({results['total_return_pct']:.2f}%)
          Initial Balance:       ${results['initial_balance']:,.2f}
          Final Balance:         ${results['final_balance']:,.2f}
          Total Fees Paid:       ${total_fees:,.2f}
        
        Risk-Adjusted Metrics:
          Sharpe Ratio:          {results['sharpe_ratio']:.3f}
          Sortino Ratio:         {results['sortino_ratio']:.3f}
          Calmar Ratio:          {results['calmar_ratio']:.3f}
          Max Drawdown:          {results['max_drawdown_pct']:.2f}%
        
        Trading Statistics:
          Total Trades:          {results['total_trades']}
          Win Rate:              {results['win_rate']:.2f}%
          Avg Profit/Trade:       ${results['avg_profit_per_trade']:,.2f}
        """
        
        ax6.text(0.1, 0.5, metrics_text, fontsize=11, family='monospace',
                verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.suptitle('Backtest Results - TradingView Style', fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Backtest results saved to {save_path}")
        plt.show()


def run_backtest_advanced(pairs: List[str] = None, 
                         start_date: str = None,
                         end_date: str = None,
                         months: int = 1,
                         years: int = 0,
                         config_path: str = "config/config.yaml",
                         random_seed: int = 42,
                         plot: bool = True):
    """
    Run advanced backtest with visualization.
    
    Args:
        pairs: List of pairs to backtest (None = use config)
        start_date: Start date string (YYYY-MM-DD) or None
        end_date: End date string (YYYY-MM-DD) or None
        months: Number of months to backtest (if dates not provided)
        years: Number of years to backtest (if dates not provided)
        config_path: Path to config file
        random_seed: Random seed for reproducible results (default: 42)
        plot: Whether to generate and show charts (default: True)
    """
    # Load config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if pairs is None:
        pairs = (config["universe"]["tier1"][:3] +  # Limit for demo
                config["universe"]["tier2"][:2])
    
    # Determine date range
    if end_date is None:
        end_date = datetime.now()
    else:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    
    if start_date is None:
        start_date = end_date - timedelta(days=30 * months + 365 * years)
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    
    logger.info(f"Backtesting from {start_date.date()} to {end_date.date()}")
    logger.info(f"Pairs: {pairs}")
    
    # Initialize backtester with fixed seed for reproducibility
    backtester = AdvancedBacktester(initial_balance=50000.0, config_path=config_path, random_seed=random_seed)
    
    # Load data
    logger.info("Loading historical data...")
    data = {}
    for pair in pairs:
        df = backtester.load_historical_data(pair, start_date, end_date)
        if len(df) > 0:
            data[pair] = df
            logger.info(f"  Loaded {len(df)} candles for {pair}")
    
    if not data:
        logger.error("No data loaded!")
        return
    
    # Run backtest
    logger.info("Running backtest...")
    results = backtester.run_backtest(data, start_date, end_date)
    
    # Display results
    print("\n" + "=" * 80)
    print("BACKTEST RESULTS")
    print("=" * 80)
    print(f"Initial Balance:     ${results['initial_balance']:,.2f}")
    print(f"Final Balance:       ${results['final_balance']:,.2f}")
    print(f"Total Return:        ${results['total_return']:,.2f} ({results['total_return_pct']:.2f}%)")
    print(f"\nRisk Metrics:")
    print(f"  Sharpe Ratio:      {results['sharpe_ratio']:.3f}")
    print(f"  Sortino Ratio:     {results['sortino_ratio']:.3f}")
    print(f"  Calmar Ratio:      {results['calmar_ratio']:.3f}")
    print(f"  Max Drawdown:      {results['max_drawdown_pct']:.2f}%")
    print(f"\nTrading Stats:")
    print(f"  Total Trades:      {results['total_trades']}")
    print(f"  Win Rate:          {results['win_rate']:.2f}%")
    print(f"  Avg Profit/Trade:  ${results['avg_profit_per_trade']:,.2f}")
    print("=" * 80)
    
    # Print detailed trade history
    print("\n" + "=" * 80)
    print("DETAILED TRADE HISTORY")
    print("=" * 80)
    
    trades = results.get('trades', [])
    if trades:
        # Filter to only closed trades (those with profit calculated)
        closed_trades = [t for t in trades if t.get('profit') is not None]
        buy_trades = [t for t in trades if t.get('action') == 'BUY']
        
        print(f"\nTotal Trades: {len(trades)} ({len(buy_trades)} buys, {len(closed_trades)} closed positions)")
        print()
        
        # Group trades by pair to show entry/exit
        trade_groups = {}
        for trade in trades:
            pair = trade['pair']
            if pair not in trade_groups:
                trade_groups[pair] = {'buys': [], 'sells': []}
            if trade['action'] == 'BUY':
                trade_groups[pair]['buys'].append(trade)
            elif trade['action'] == 'SELL':
                trade_groups[pair]['sells'].append(trade)
        
        # Show closed trades with P&L
        print("CLOSED POSITIONS (with P&L):")
        print("-" * 80)
        closed_count = 0
        for pair, group in trade_groups.items():
            for sell in group['sells']:
                if sell.get('profit') is not None:
                    closed_count += 1
                    entry_price = sell.get('entry_price', 0)
                    exit_price = sell['price']
                    qty = sell['quantity']
                    fee = sell.get('fee', 0)
                    profit = sell['profit']
                    pnl_pct = sell.get('pnl_pct', 0)
                    timestamp = sell['timestamp']
                    
                    print(f"\nTrade #{closed_count}: {pair}")
                    print(f"  Entry:    {qty:.6f} @ ${entry_price:.2f} (${entry_price*qty:,.2f})")
                    print(f"  Exit:     {qty:.6f} @ ${exit_price:.2f} (${exit_price*qty:,.2f})")
                    print(f"  Date:     {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"  Fee:      ${fee:.2f}")
                    print(f"  P&L:      ${profit:,.2f} ({pnl_pct:+.2f}%)")
        
        if closed_count == 0:
            print("  (No closed positions - all positions still open)")
        
        # Show all buy/sell trades
        print("\n" + "=" * 80)
        print("ALL TRADES (Chronological):")
        print("-" * 80)
        print(f"{'#':<4} {'Time':<20} {'Action':<6} {'Pair':<12} {'Qty':<12} {'Price':<12} {'Fee':<8} {'P&L':<12}")
        print("-" * 80)
        
        sorted_trades = sorted(trades, key=lambda x: x['timestamp'])
        for i, trade in enumerate(sorted_trades, 1):
            action = trade['action']
            pair = trade['pair']
            qty = trade['quantity']
            price = trade['price']
            fee = trade.get('fee', 0)
            profit = trade.get('profit', None)
            timestamp = trade['timestamp']
            
            pnl_str = f"${profit:,.2f}" if profit is not None else "N/A"
            if profit is not None:
                pnl_pct = trade.get('pnl_pct', 0)
                pnl_str += f" ({pnl_pct:+.2f}%)"
            
            print(f"{i:<4} {timestamp.strftime('%Y-%m-%d %H:%M'):<20} {action:<6} {pair:<12} {qty:<12.6f} ${price:<11.2f} ${fee:<7.2f} {pnl_str}")
        
        print("=" * 80)
    else:
        print("No trades executed.")
    
    print("=" * 80)
    
    # Create visualization only if requested
    if plot:
        logger.info("Generating charts...")
        backtester.plot_results(results, data, pair_to_plot=pairs[0] if pairs else 'BTC/USD')
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Advanced Backtesting with Visualization')
    parser.add_argument('--pairs', nargs='+', help='Trading pairs to backtest')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--months', type=int, default=1, help='Number of months to backtest')
    parser.add_argument('--years', type=int, default=0, help='Number of years to backtest')
    parser.add_argument('--config', type=str, default='config/config.yaml', help='Config file path')
    
    args = parser.parse_args()
    
    run_backtest_advanced(
        pairs=args.pairs,
        start_date=args.start,
        end_date=args.end,
        months=args.months,
        years=args.years,
        config_path=args.config
    )

