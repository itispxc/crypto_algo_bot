"""
Trading strategy implementations.
Simple moving average crossover strategy.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class MovingAverageStrategy:
    """
    Simple Moving Average Crossover Strategy.
    
    Buy signal: Fast MA crosses above Slow MA
    Sell signal: Fast MA crosses below Slow MA
    """
    
    def __init__(self, fast_period: int = 10, slow_period: int = 30):
        """
        Initialize the strategy.
        
        Args:
            fast_period: Period for fast moving average
            slow_period: Period for slow moving average
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.previous_signal = None
    
    def calculate_indicators(self, klines: List[Dict]) -> pd.DataFrame:
        """
        Calculate technical indicators from kline data.
        
        Args:
            klines: List of kline/candlestick data (can be list of lists or list of dicts)
            
        Returns:
            DataFrame with price data and indicators
        """
        if not klines or len(klines) < self.slow_period:
            logger.warning(f"Insufficient data: {len(klines)} candles, need at least {self.slow_period}")
            return pd.DataFrame()
        
        # Handle different kline formats
        # Format 1: List of lists [timestamp, open, high, low, close, volume, ...]
        # Format 2: List of dicts [{'timestamp': ..., 'open': ..., ...}, ...]
        if isinstance(klines[0], list):
            # List of lists format
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume'
            ])
        elif isinstance(klines[0], dict):
            # List of dicts format
            df = pd.DataFrame(klines)
            # Normalize column names (handle different API formats)
            if 'close_price' in df.columns:
                df['close'] = df['close_price']
            if 'closePrice' in df.columns:
                df['close'] = df['closePrice']
            if 'c' in df.columns:
                df['close'] = df['c']
        else:
            logger.error(f"Unknown kline format: {type(klines[0])}")
            return pd.DataFrame()
        
        # Ensure we have a 'close' column
        if 'close' not in df.columns:
            logger.error("Could not find 'close' price column in kline data")
            return pd.DataFrame()
        
        # Convert to numeric
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Calculate moving averages
        df['fast_ma'] = df['close'].rolling(window=self.fast_period).mean()
        df['slow_ma'] = df['close'].rolling(window=self.slow_period).mean()
        
        # Calculate signal
        df['signal'] = 0  # 0 = hold, 1 = buy, -1 = sell
        
        # Buy signal: fast MA crosses above slow MA
        df.loc[df['fast_ma'] > df['slow_ma'], 'signal'] = 1
        
        # Sell signal: fast MA crosses below slow MA
        df.loc[df['fast_ma'] < df['slow_ma'], 'signal'] = -1
        
        # Detect crossovers
        df['prev_fast'] = df['fast_ma'].shift(1)
        df['prev_slow'] = df['slow_ma'].shift(1)
        
        # Generate crossover signals
        df['crossover'] = 0
        # Bullish crossover: fast crosses above slow
        bullish_cross = (df['prev_fast'] <= df['prev_slow']) & (df['fast_ma'] > df['slow_ma'])
        # Bearish crossover: fast crosses below slow
        bearish_cross = (df['prev_fast'] >= df['prev_slow']) & (df['fast_ma'] < df['slow_ma'])
        
        df.loc[bullish_cross, 'crossover'] = 1  # Buy signal
        df.loc[bearish_cross, 'crossover'] = -1  # Sell signal
        
        return df
    
    def get_signal(self, klines: List[Dict]) -> str:
        """
        Get trading signal based on current market data.
        
        Args:
            klines: List of kline/candlestick data
            
        Returns:
            Trading signal: 'buy', 'sell', or 'hold'
        """
        df = self.calculate_indicators(klines)
        
        if df.empty or len(df) < self.slow_period:
            logger.warning("Insufficient data for signal generation")
            return 'hold'
        
        # Get the latest data point
        latest = df.iloc[-1]
        
        # Check for crossover signals
        if latest['crossover'] == 1:
            logger.info("Bullish crossover detected - BUY signal")
            self.previous_signal = 'buy'
            return 'buy'
        elif latest['crossover'] == -1:
            logger.info("Bearish crossover detected - SELL signal")
            self.previous_signal = 'sell'
            return 'sell'
        
        # Check current trend
        if latest['fast_ma'] > latest['slow_ma']:
            # Uptrend but no crossover - hold if we have position, buy if we don't
            if self.previous_signal == 'sell' or self.previous_signal is None:
                return 'hold'
            return 'hold'
        else:
            # Downtrend but no crossover - hold if we have position, sell if we don't
            if self.previous_signal == 'buy':
                return 'hold'
            return 'hold'
    
    def get_position_size(self, balance: float, price: float, 
                         max_position_pct: float = 0.1) -> float:
        """
        Calculate position size based on risk management rules.
        
        Args:
            balance: Available balance
            price: Current price
            max_position_pct: Maximum position as percentage of balance
            
        Returns:
            Position size in base currency
        """
        max_position_value = balance * max_position_pct
        position_size = max_position_value / price
        
        logger.info(f"Calculated position size: {position_size:.6f} (max: {max_position_pct*100}% of balance)")
        return position_size

