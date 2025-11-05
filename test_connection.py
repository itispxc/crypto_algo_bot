"""
Test script to verify Roostoo API connection and credentials.
"""
import logging
import sys
from config import Config
from roostoo_client import RoostooClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_connection():
    """Test API connection and basic endpoints."""
    config = Config()
    
    logger.info("Testing Roostoo API connection...")
    logger.info(f"API Key: {config.ROOSTOO_API_KEY[:10]}...")
    logger.info(f"Base URL: {config.ROOSTOO_BASE_URL}")
    
    client = RoostooClient(
        api_key=config.ROOSTOO_API_KEY,
        api_secret=config.ROOSTOO_API_SECRET,
        base_url=config.ROOSTOO_BASE_URL
    )
    
    try:
        # Test signed endpoints (these are the main ones we need)
        logger.info("Testing signed endpoints (these require authentication)...")
        
        # Test balance endpoint (most important for trading)
        logger.info("Testing balance endpoint...")
        try:
            balance = client.get_balance()
            logger.info(f"✓ Balance: {balance}")
        except Exception as e:
            logger.error(f"✗ Balance endpoint failed: {str(e)}")
            raise
        
        # Test portfolio endpoint (uses balance)
        logger.info("Testing portfolio endpoint...")
        try:
            portfolio = client.get_portfolio()
            logger.info(f"✓ Portfolio: {portfolio}")
        except Exception as e:
            logger.warning(f"Portfolio endpoint issue: {str(e)}")
        
        # Test pending order count
        logger.info("Testing pending order count endpoint...")
        try:
            pending_count = client.get_pending_order_count()
            logger.info(f"✓ Pending order count: {pending_count}")
        except Exception as e:
            logger.warning(f"Pending order count issue: {str(e)}")
        
        # Test query orders
        logger.info("Testing query order endpoint...")
        try:
            orders = client.query_order(limit=5)
            logger.info(f"✓ Query orders: {orders}")
        except Exception as e:
            logger.warning(f"Query orders issue: {str(e)}")
        
        logger.info("\n" + "="*50)
        logger.info("✓ Core API endpoints tested!")
        logger.info("Balance endpoint is working - bot can proceed")
        logger.info("="*50)
        return True
        
    except Exception as e:
        logger.error(f"✗ Connection test failed: {str(e)}")
        logger.error("Please check:")
        logger.error("1. API credentials are correct")
        logger.error("2. API base URL is correct")
        logger.error("3. Network connectivity")
        logger.error("4. API endpoint paths match Roostoo documentation")
        return False


if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)

