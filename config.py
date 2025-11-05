"""
Configuration management for the trading bot.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Bot configuration settings."""
    
    # API Credentials
    ROOSTOO_API_KEY = os.getenv('ROOSTOO_API_KEY', 'Qqaqe0nsBMoPzhRvusONKFh5kARjTSkoG9zxG0HVuXQcnBGPmuWMXjRxBTXhe30o')
    ROOSTOO_API_SECRET = os.getenv('ROOSTOO_API_SECRET', 'CTaBKUVDOZCwxrQCMeAXFMWxpDFXsHmS0qfnNjvlO7IPBc57jV5cVXqFX3zj6qv6')
    
    # API Base URL
    ROOSTOO_BASE_URL = os.getenv('ROOSTOO_BASE_URL', 'https://mock-api.roostoo.com')
    
    # Trading Parameters
    TRADING_PAIR = 'BTC/USD'  # Default trading pair (Roostoo uses USD, not USDT)
    MIN_ORDER_SIZE = 0.001  # Minimum order size
    MAX_POSITION_SIZE = 0.1  # Maximum position as fraction of portfolio
    TRADING_INTERVAL = 60  # Trading interval in seconds
    
    # Strategy Parameters
    FAST_MA_PERIOD = 10  # Fast moving average period
    SLOW_MA_PERIOD = 30  # Slow moving average period
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Risk Management
    STOP_LOSS_PERCENT = 0.02  # 2% stop loss
    TAKE_PROFIT_PERCENT = 0.05  # 5% take profit

