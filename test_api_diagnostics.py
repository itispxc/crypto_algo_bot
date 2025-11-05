"""
Comprehensive API diagnostics to help identify connection issues.
"""
import requests
import time
import logging
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_basic_connectivity(base_url: str):
    """Test basic HTTPS connectivity to the base URL."""
    logger.info(f"Testing basic connectivity to {base_url}...")
    
    try:
        # Try connecting to the base domain
        domain = base_url.replace('https://', '').replace('http://', '').split('/')[0]
        response = requests.get(f"https://{domain}", timeout=5)
        logger.info(f"✓ Basic connectivity OK: Status {response.status_code}")
        return True
    except requests.exceptions.Timeout:
        logger.error(f"✗ Connection timeout - server may be unreachable")
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error(f"✗ Connection error: {str(e)}")
        return False
    except Exception as e:
        logger.warning(f"⚠ Unexpected response: {str(e)}")
        return False


def test_endpoint_variations(base_url: str, api_key: str, api_secret: str):
    """Test various possible endpoint paths."""
    from roostoo_client import RoostooClient
    
    # Common endpoint variations
    endpoints_to_test = [
        '/api/v1/portfolio',
        '/api/portfolio',
        '/v1/portfolio',
        '/portfolio',
        '/api/v1/account',
        '/api/account',
        '/v1/account',
        '/account',
    ]
    
    logger.info("Testing various endpoint paths...")
    
    for endpoint in endpoints_to_test:
        try:
            logger.info(f"  Trying: {endpoint}")
            client = RoostooClient(api_key, api_secret, base_url)
            
            # Try a simple GET request
            url = f"{base_url}{endpoint}"
            timestamp = int(time.time() * 1000)
            
            # Simple test without full auth for now
            headers = {
                'X-API-Key': api_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            logger.info(f"    Status: {response.status_code}")
            if response.status_code != 404:
                logger.info(f"    Response: {response.text[:200]}")
                if response.status_code == 200:
                    logger.info(f"  ✓ Found working endpoint: {endpoint}")
                    return endpoint
        except requests.exceptions.Timeout:
            logger.warning(f"    Timeout")
        except Exception as e:
            logger.warning(f"    Error: {str(e)[:100]}")
    
    return None


def test_simple_request(base_url: str, api_key: str):
    """Test a simple request without authentication."""
    logger.info("Testing simple request without auth...")
    
    try:
        url = f"{base_url}/api/v1/portfolio"
        response = requests.get(url, timeout=5)
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response: {response.text[:500]}")
    except Exception as e:
        logger.error(f"Error: {str(e)}")


def main():
    """Run comprehensive diagnostics."""
    config = Config()
    
    logger.info("=" * 60)
    logger.info("Roostoo API Diagnostics")
    logger.info("=" * 60)
    logger.info(f"Base URL: {config.ROOSTOO_BASE_URL}")
    logger.info(f"API Key: {config.ROOSTOO_API_KEY[:15]}...")
    logger.info("")
    
    # Test 1: Basic connectivity
    if not test_basic_connectivity(config.ROOSTOO_BASE_URL):
        logger.error("\n✗ Cannot reach the server. Possible issues:")
        logger.error("  1. Incorrect base URL")
        logger.error("  2. Network/firewall blocking connection")
        logger.error("  3. Server is down")
        logger.error("\nPlease check:")
        logger.error(f"  - Verify the base URL: {config.ROOSTOO_BASE_URL}")
        logger.error("  - Check Roostoo API documentation for correct URL")
        logger.error("  - Try accessing the URL in a browser")
        return
    
    logger.info("")
    
    # Test 2: Simple request
    test_simple_request(config.ROOSTOO_BASE_URL, config.ROOSTOO_API_KEY)
    
    logger.info("")
    
    # Test 3: Endpoint variations
    working_endpoint = test_endpoint_variations(
        config.ROOSTOO_BASE_URL,
        config.ROOSTOO_API_KEY,
        config.ROOSTOO_API_SECRET
    )
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("Diagnostics Complete")
    logger.info("=" * 60)
    
    if working_endpoint:
        logger.info(f"✓ Found working endpoint: {working_endpoint}")
        logger.info("Update roostoo_client.py to use this endpoint")
    else:
        logger.info("⚠ No working endpoints found")
        logger.info("Please check:")
        logger.info("  1. Roostoo API documentation for correct endpoints")
        logger.info("  2. API authentication method")
        logger.info("  3. Network connectivity")


if __name__ == '__main__':
    main()

