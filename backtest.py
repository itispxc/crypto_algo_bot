"""
Backtesting script for the moving average crossover strategy.
Tests the strategy on historical data to evaluate profitability.
"""
import pandas as pd
import numpy as np
from typing import List, Dict
import logging
from datetime import datetime, timedelta
from strategy import MovingAverageStrategy
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Backtester:
    """Backtesting engine for trading strategies."""
    
    def __init__(self, initial_balance: float = 50000.0):
        """
        Initialize backtester.
        
        Args:
            initial_balance: Starting balance in USD
        """
        self.config = Config()
        self.strategy = MovingAverageStrategy(
            fast_period=self.config.FAST_MA_PERIOD,
            slow_period=self.config.SLOW_MA_PERIOD
        )
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position = None  # {'amount': float, 'entry_price': float}
        self.trades = []
        self.equity_curve = []
    
    def generate_sample_data(self, days: int = 30, initial_price: float = 50000.0) -> pd.DataFrame:
        """
        Generate sample historical price data for backtesting.
        Uses a random walk with trend to simulate realistic price movements.
        
        Args:
            days: Number of days of data
            initial_price: Starting price
            
        Returns:
            DataFrame with OHLCV data
        """
        logger.info(f"Generating {days} days of sample data...")
        
        # Generate timestamps (1-minute candles)
        periods = days * 24 * 60  # days * hours * minutes
        timestamps = pd.date_range(
            end=datetime.now(),
            periods=periods,
            freq='1min'
        )
        
        # Generate price data using random walk with slight trend
        np.random.seed(42)  # For reproducibility
        returns = np.random.normal(0.0001, 0.01, periods)  # Small positive drift
        
        prices = [initial_price]
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Create OHLCV data
        data = []
        for i, (ts, price) in enumerate(zip(timestamps, prices)):
            # Simple OHLC from price
            high = price * (1 + abs(np.random.normal(0, 0.002)))
            low = price * (1 - abs(np.random.normal(0, 0.002)))
            open_price = prices[i-1] if i > 0 else price
            volume = np.random.uniform(100, 1000)
            
            data.append({
                'timestamp': int(ts.timestamp() * 1000),
                'open': open_price,
                'high': high,
                'low': low,
                'close': price,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        return df
    
    def load_historical_data(self, file_path: str) -> pd.DataFrame:
        """
        Load historical data from a CSV file.
        
        Expected format: timestamp,open,high,low,close,volume
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            df = pd.read_csv(file_path)
            # Ensure timestamp is in milliseconds
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_numeric(df['timestamp'])
            return df
        except Exception as e:
            logger.error(f"Failed to load data from {file_path}: {str(e)}")
            return pd.DataFrame()
    
    def execute_trade(self, signal: str, price: float, timestamp: datetime):
        """
        Execute a trade in the backtest.
        
        Args:
            signal: 'buy' or 'sell'
            price: Current price
            timestamp: Trade timestamp
        """
        if signal == 'buy' and self.position is None:
            # Calculate position size (10% of balance)
            max_position_value = self.balance * self.config.MAX_POSITION_SIZE
            amount = max_position_value / price
            
            if amount > 0:
                cost = amount * price
                if cost <= self.balance:
                    self.position = {
                        'amount': amount,
                        'entry_price': price,
                        'entry_time': timestamp
                    }
                    self.balance -= cost
                    
                    self.trades.append({
                        'timestamp': timestamp,
                        'action': 'BUY',
                        'price': price,
                        'amount': amount,
                        'cost': cost,
                        'balance': self.balance
                    })
                    logger.debug(f"BUY: {amount:.6f} @ ${price:.2f}, Cost: ${cost:.2f}, Balance: ${self.balance:.2f}")
        
        elif signal == 'sell' and self.position is not None:
            # Close position
            amount = self.position['amount']
            revenue = amount * price
            profit = revenue - (amount * self.position['entry_price'])
            
            self.balance += revenue
            entry_price = self.position['entry_price']
            
            self.trades.append({
                'timestamp': timestamp,
                'action': 'SELL',
                'price': price,
                'amount': amount,
                'revenue': revenue,
                'profit': profit,
                'balance': self.balance,
                'return_pct': (profit / (amount * entry_price)) * 100
            })
            
            logger.debug(f"SELL: {amount:.6f} @ ${price:.2f}, Revenue: ${revenue:.2f}, Profit: ${profit:.2f}, Balance: ${self.balance:.2f}")
            
            self.position = None
    
    def run_backtest(self, data: pd.DataFrame) -> Dict:
        """
        Run backtest on historical data.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Backtest results dictionary
        """
        logger.info("Starting backtest...")
        logger.info(f"Data points: {len(data)}")
        logger.info(f"Initial balance: ${self.initial_balance:,.2f}")
        
        # Convert data to list of dicts for strategy
        klines = data.to_dict('records')
        
        # Process each candle
        for i in range(self.config.SLOW_MA_PERIOD, len(data)):
            # Get data up to current point
            current_data = klines[:i+1]
            
            # Get signal from strategy
            signal = self.strategy.get_signal(current_data)
            
            # Get current price
            current_price = data.iloc[i]['close']
            current_time = datetime.fromtimestamp(data.iloc[i]['timestamp'] / 1000)
            
            # Execute trade if signal
            if signal in ['buy', 'sell']:
                self.execute_trade(signal, current_price, current_time)
            
            # Track equity curve
            current_equity = self.balance
            if self.position:
                # Add unrealized P&L
                current_equity += self.position['amount'] * current_price
            
            self.equity_curve.append({
                'timestamp': current_time,
                'equity': current_equity,
                'price': current_price
            })
        
        # Close any open position at the end
        if self.position:
            final_price = data.iloc[-1]['close']
            final_time = datetime.fromtimestamp(data.iloc[-1]['timestamp'] / 1000)
            self.execute_trade('sell', final_price, final_time)
        
        # Calculate results
        results = self.calculate_results()
        return results
    
    def calculate_results(self) -> Dict:
        """
        Calculate backtest performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'final_balance': self.initial_balance,
                'total_return': 0,
                'total_return_pct': 0,
                'win_rate': 0,
                'avg_profit': 0,
                'max_drawdown': 0
            }
        
        # Calculate returns
        total_return = self.balance - self.initial_balance
        total_return_pct = (total_return / self.initial_balance) * 100
        
        # Calculate win rate
        profitable_trades = [t for t in self.trades if t.get('profit', 0) > 0]
        win_rate = (len(profitable_trades) / len(self.trades)) * 100 if self.trades else 0
        
        # Average profit per trade
        profits = [t.get('profit', 0) for t in self.trades if 'profit' in t]
        avg_profit = np.mean(profits) if profits else 0
        
        # Maximum drawdown
        equity_values = [e['equity'] for e in self.equity_curve]
        if equity_values:
            peak = equity_values[0]
            max_dd = 0
            for equity in equity_values:
                if equity > peak:
                    peak = equity
                dd = (peak - equity) / peak * 100
                if dd > max_dd:
                    max_dd = dd
        else:
            max_dd = 0
        
        results = {
            'total_trades': len(self.trades),
            'initial_balance': self.initial_balance,
            'final_balance': self.balance,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'max_drawdown': max_dd,
            'trades': self.trades
        }
        
        return results
    
    def print_results(self, results: Dict):
        """Print backtest results in a readable format."""
        print("\n" + "=" * 60)
        print("BACKTEST RESULTS")
        print("=" * 60)
        print(f"Initial Balance:     ${results['initial_balance']:,.2f}")
        print(f"Final Balance:       ${results['final_balance']:,.2f}")
        print(f"Total Return:        ${results['total_return']:,.2f}")
        print(f"Total Return %:      {results['total_return_pct']:.2f}%")
        print(f"Total Trades:        {results['total_trades']}")
        print(f"Win Rate:            {results['win_rate']:.2f}%")
        print(f"Avg Profit/Trade:   ${results['avg_profit']:,.2f}")
        print(f"Max Drawdown:        {results['max_drawdown']:.2f}%")
        print("=" * 60)
        
        if results['trades']:
            print("\nRecent Trades:")
            for trade in results['trades'][-10:]:  # Last 10 trades
                if 'profit' in trade:
                    print(f"  {trade['action']}: {trade['amount']:.6f} @ ${trade['price']:.2f} "
                          f"| Profit: ${trade['profit']:.2f} ({trade.get('return_pct', 0):.2f}%)")
                else:
                    print(f"  {trade['action']}: {trade['amount']:.6f} @ ${trade['price']:.2f}")


def main():
    """Run backtest."""
    config = Config()
    
    print("=" * 60)
    print("TRADING BOT BACKTEST")
    print("=" * 60)
    print(f"Strategy: Moving Average Crossover")
    print(f"Fast MA: {config.FAST_MA_PERIOD}, Slow MA: {config.SLOW_MA_PERIOD}")
    print(f"Trading Pair: {config.TRADING_PAIR}")
    print()
    
    # Create backtester
    backtester = Backtester(initial_balance=50000.0)
    
    # Generate sample data (or load from file if available)
    print("Generating sample historical data...")
    data = backtester.generate_sample_data(days=30, initial_price=50000.0)
    
    # Alternative: Load from file if you have real data
    # data = backtester.load_historical_data('historical_data.csv')
    
    # Run backtest
    results = backtester.run_backtest(data)
    
    # Print results
    backtester.print_results(results)
    
    # Interpretation
    print("\n" + "=" * 60)
    print("INTERPRETATION")
    print("=" * 60)
    if results['total_return_pct'] > 0:
        print(f"✓ Strategy is profitable: {results['total_return_pct']:.2f}% return")
        if results['total_return_pct'] > 5:
            print("  Strong performance!")
        elif results['total_return_pct'] > 2:
            print("  Moderate performance")
        else:
            print("  Weak but positive performance")
    else:
        print(f"✗ Strategy lost money: {results['total_return_pct']:.2f}% return")
        print("  Consider adjusting strategy parameters")
    
    if results['win_rate'] > 50:
        print(f"✓ Good win rate: {results['win_rate']:.2f}%")
    else:
        print(f"⚠ Low win rate: {results['win_rate']:.2f}%")
    
    if results['max_drawdown'] > 20:
        print(f"⚠ High drawdown: {results['max_drawdown']:.2f}% - High risk!")
    elif results['max_drawdown'] > 10:
        print(f"⚠ Moderate drawdown: {results['max_drawdown']:.2f}%")
    else:
        print(f"✓ Low drawdown: {results['max_drawdown']:.2f}% - Good risk control")
    
    print("\nNext Steps:")
    print("1. If profitable, test with mock API (run: python main.py)")
    print("2. If not profitable, adjust strategy parameters in config.py")
    print("3. Once satisfied, deploy to AWS EC2")
    print("=" * 60)


if __name__ == '__main__':
    main()

