"""
Main entry point for the trading bot.
"""
import logging
import sys
from trading_bot import TradingBot

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('trading_bot.log')
        ]
    )

def main():
    """Main function to start the trading bot."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("Crypto Trading Bot - Starting")
    logger.info("=" * 60)
    
    try:
        bot = TradingBot()
        bot.run()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()

