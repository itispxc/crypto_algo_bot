"""
Main trading bot orchestrator.
Manages portfolio, executes trades, and monitors performance.
"""
import time
import logging
from typing import Dict, Optional
from datetime import datetime

from config import Config
from roostoo_client import RoostooClient
from strategy import MovingAverageStrategy

logger = logging.getLogger(__name__)


class TradingBot:
    """
    Main trading bot that orchestrates strategy execution and trade management.
    """
    
    def __init__(self):
        """Initialize the trading bot."""
        self.config = Config()
        self.client = RoostooClient(
            api_key=self.config.ROOSTOO_API_KEY,
            api_secret=self.config.ROOSTOO_API_SECRET,
            base_url=self.config.ROOSTOO_BASE_URL
        )
        self.strategy = MovingAverageStrategy(
            fast_period=self.config.FAST_MA_PERIOD,
            slow_period=self.config.SLOW_MA_PERIOD
        )
        self.running = False
        self.current_position = None
        self.last_trade_time = None
    
    def get_portfolio_summary(self) -> Dict:
        """
        Get and summarize current portfolio status.
        
        Returns:
            Portfolio summary dictionary
        """
        try:
            portfolio = self.client.get_portfolio()
            balance = self.client.get_balance()
            
            summary = {
                'timestamp': datetime.now().isoformat(),
                'portfolio': portfolio,
                'balance': balance,
                'total_balance': balance.get('total', 0) if isinstance(balance, dict) else 0,
                'available_balance': balance.get('available', 0) if isinstance(balance, dict) else 0
            }
            
            logger.info(f"Portfolio Summary: {summary}")
            return summary
        except Exception as e:
            logger.error(f"Failed to get portfolio summary: {str(e)}")
            return {}
    
    def get_current_price(self, pair: str) -> Optional[float]:
        """
        Get current price for a trading pair.
        
        Args:
            pair: Trading pair (e.g., 'BTC/USD')
            
        Returns:
            Current price or None if failed
        """
        try:
            ticker = self.client.get_ticker(pair)
            # Extract price from ticker response
            # Handle different API response formats
            if isinstance(ticker, dict):
                # Try common price field names from Roostoo API
                price = (ticker.get('price') or ticker.get('last') or 
                        ticker.get('close') or ticker.get('lastPrice') or
                        ticker.get('close_price') or ticker.get('c') or
                        ticker.get('Price') or ticker.get('Last'))
                if price:
                    return float(price)
            elif isinstance(ticker, (int, float)):
                # If ticker is directly a price
                return float(ticker)
            return None
        except Exception as e:
            logger.error(f"Failed to get current price: {str(e)}")
            return None
    
    def check_position(self, pair: str) -> Dict:
        """
        Check current position for a trading pair.
        
        Args:
            pair: Trading pair (e.g., 'BTC/USD')
            
        Returns:
            Position information
        """
        try:
            # Query orders to check for open positions
            orders = self.client.query_order(pair=pair, pending_only=True)
            if orders and orders.get('Success'):
                order_list = orders.get('OrderMatched', [])
                # Return first pending order as position indicator
                if order_list:
                    return order_list[0]
            return {}
        except Exception as e:
            logger.error(f"Failed to check position: {str(e)}")
            return {}
    
    def execute_trade(self, signal: str, pair: str, amount: Optional[float] = None) -> bool:
        """
        Execute a trade based on signal.
        
        Args:
            signal: Trading signal ('buy', 'sell', 'hold')
            symbol: Trading pair symbol
            amount: Trade amount (optional, calculated if not provided)
            
        Returns:
            True if trade executed successfully, False otherwise
        """
        if signal == 'hold':
            return False
        
        try:
            # Get current price
            price = self.get_current_price(pair)
            if not price:
                logger.error("Failed to get current price, skipping trade")
                return False
            
            # Get portfolio balance
            portfolio = self.get_portfolio_summary()
            # Extract balance from Roostoo API response format
            balance_data = portfolio.get('balance', {})
            if isinstance(balance_data, dict) and balance_data.get('Success'):
                # Roostoo API format: SpotWallet -> USD -> Free
                spot_wallet = balance_data.get('SpotWallet', {})
                usd_balance = spot_wallet.get('USD', {})
                available_balance = float(usd_balance.get('Free', 0))
            else:
                available_balance = 0
            
            if signal == 'buy':
                # Calculate buy amount
                if amount is None:
                    amount = self.strategy.get_position_size(
                        available_balance,
                        price,
                        self.config.MAX_POSITION_SIZE
                    )
                
                # Check minimum order size
                if amount < self.config.MIN_ORDER_SIZE:
                    logger.warning(f"Amount {amount} below minimum order size {self.config.MIN_ORDER_SIZE}")
                    return False
                
                # Check if we have enough balance
                required_balance = amount * price
                if required_balance > available_balance:
                    logger.warning(f"Insufficient balance: need {required_balance}, have {available_balance}")
                    return False
                
                # Place buy order (MARKET order - no price needed)
                logger.info(f"Executing BUY order: {amount} {pair} at ~{price}")
                order = self.client.place_order(
                    pair=pair,
                    side='BUY',
                    quantity=amount
                    # No price = MARKET order
                )
                
                if order and order.get('Success'):
                    self.current_position = {
                        'pair': pair,
                        'side': 'long',
                        'amount': amount,
                        'entry_price': price,
                        'entry_time': datetime.now()
                    }
                    self.last_trade_time = time.time()
                    logger.info(f"BUY order executed: {order}")
                    return True
                else:
                    logger.error(f"Order failed: {order.get('ErrMsg', 'Unknown error')}")
                    return False
            
            elif signal == 'sell':
                # Check if we have a position
                position = self.check_position(pair)
                
                if not position:
                    logger.warning("No position to sell")
                    return False
                
                # Get position amount from order
                if amount is None:
                    amount = float(position.get('Quantity', position.get('quantity', 0)))
                
                if amount <= 0:
                    logger.warning("Invalid sell amount")
                    return False
                
                # Place sell order (MARKET order - no price needed)
                logger.info(f"Executing SELL order: {amount} {pair} at ~{price}")
                order = self.client.place_order(
                    pair=pair,
                    side='SELL',
                    quantity=amount
                    # No price = MARKET order
                )
                
                if order and order.get('Success'):
                    self.current_position = None
                    self.last_trade_time = time.time()
                    logger.info(f"SELL order executed: {order}")
                    return True
                else:
                    logger.error(f"Order failed: {order.get('ErrMsg', 'Unknown error')}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to execute trade: {str(e)}")
            return False
    
    def run_iteration(self):
        """Run one iteration of the trading bot logic."""
        try:
            logger.info("=" * 50)
            logger.info("Starting trading bot iteration")
            
            # Get portfolio summary
            portfolio = self.get_portfolio_summary()
            logger.info(f"Portfolio: {portfolio}")
            
            # Get market data
            pair = self.config.TRADING_PAIR
            logger.info(f"Fetching market data for {pair}")
            
            # Get ticker data (klines may not be available)
            ticker = self.client.get_ticker(pair)
            
            # For now, use a simplified approach since klines may not be available
            # We'll use ticker data to make basic decisions
            # In a production system, you'd want to implement proper candlestick data collection
            logger.info(f"Ticker data: {ticker}")
            
            # For strategy, we'll need to adapt - for now, use a simple price-based approach
            # Get current price
            current_price = self.get_current_price(pair)
            if current_price:
                logger.info(f"Current price: {current_price}")
                
                # Simple strategy: check if we have a position
                position = self.check_position(pair)
                if position:
                    # If we have a position, consider selling (simple logic)
                    # In real implementation, use proper technical analysis
                    logger.info("Position detected, checking exit conditions...")
                    # For now, just hold
                    signal = 'hold'
                else:
                    # No position, could buy (but we need proper signals)
                    # For now, hold until proper klines data is available
                    logger.info("No position, waiting for proper market data...")
                    signal = 'hold'
            else:
                signal = 'hold'
            
            logger.info(f"Strategy signal: {signal}")
            
            # Execute trade based on signal
            if signal in ['buy', 'sell']:
                self.execute_trade(signal, pair)
            else:
                logger.info("Hold signal - no trade executed")
            
            # Log current status
            position = self.check_position(pair)
            logger.info(f"Current position: {position}")
            
        except Exception as e:
            logger.error(f"Error in trading bot iteration: {str(e)}", exc_info=True)
    
    def run(self):
        """Main bot loop."""
        logger.info("Starting trading bot...")
        logger.info(f"Configuration: {self.config.TRADING_PAIR}, "
                   f"Fast MA: {self.config.FAST_MA_PERIOD}, "
                   f"Slow MA: {self.config.SLOW_MA_PERIOD}")
        
        self.running = True
        
        try:
            while self.running:
                self.run_iteration()
                
                # Wait before next iteration
                logger.info(f"Waiting {self.config.TRADING_INTERVAL} seconds before next iteration...")
                time.sleep(self.config.TRADING_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("Trading bot stopped by user")
            self.running = False
        except Exception as e:
            logger.error(f"Trading bot error: {str(e)}", exc_info=True)
            self.running = False
    
    def stop(self):
        """Stop the trading bot."""
        logger.info("Stopping trading bot...")
        self.running = False

