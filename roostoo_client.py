"""
Roostoo API Client for trading bot operations.
Handles authentication, portfolio queries, and trade execution.
Based on official Roostoo API documentation: https://github.com/roostoo/Roostoo-API-Documents
"""
import requests
import time
import hmac
import hashlib
import base64
import urllib.parse
from typing import Dict, List, Optional
import logging

from config import Config

logger = logging.getLogger(__name__)


class RoostooClient:
    """Client for interacting with Roostoo exchange API."""
    
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        """
        Initialize Roostoo API client.
        
        Args:
            api_key: API key for authentication
            api_secret: API secret for authentication
            base_url: Base URL for the API
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def _generate_signature(self, payload: Dict) -> str:
        """
        Generate signature for Roostoo API authentication.
        Uses hex digest (not base64) as shown in demo code.
        
        Args:
            payload: Dictionary of parameters
            
        Returns:
            Hex signature string
        """
        # Create query string: key=value&key2=value2 (sorted)
        query_string = '&'.join(["{}={}".format(k, payload[k]) 
                                for k in sorted(payload.keys())])
        
        # Generate HMAC SHA256 signature (hex format)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _get_signed_headers(self, payload: Dict, use_milliseconds: bool = True) -> tuple:
        """
        Generate signed headers for RCL_TopLevelCheck authentication.
        
        Args:
            payload: Dictionary of parameters
            use_milliseconds: Whether to use millisecond timestamp (True) or seconds (False)
            
        Returns:
            Tuple of (headers dict, final payload dict)
        """
        # Add timestamp (milliseconds for signed endpoints, seconds for some public)
        if use_milliseconds:
            payload['timestamp'] = int(time.time() * 1000)
        else:
            payload['timestamp'] = int(time.time())
        
        # Generate signature
        signature = self._generate_signature(payload)
        
        # Create headers
        headers = {
            'RST-API-KEY': self.api_key,
            'MSG-SIGNATURE': signature
        }
        
        return headers, payload
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None, use_milliseconds: bool = True) -> Dict:
        """
        Make authenticated API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint path
            params: Query parameters (for GET requests)
            data: Request body data (for POST requests)
            use_milliseconds: Whether to use millisecond timestamp
            
        Returns:
            JSON response as dictionary
            
        Raises:
            Exception: If API request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        # Prepare payload based on method
        if method == 'GET':
            payload = params or {}
        elif method == 'POST':
            payload = data or {}
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        # Generate signed headers
        headers, final_payload = self._get_signed_headers(payload, use_milliseconds)
        
        try:
            if method == 'GET':
                # For GET, use params and signature in headers
                response = self.session.get(
                    url, 
                    headers=headers, 
                    params=final_payload, 
                    timeout=30
                )
            elif method == 'POST':
                # For POST, use form data (not JSON)
                response = self.session.post(
                    url,
                    headers=headers,
                    data=final_payload,  # Form data dict, requests will encode it
                    timeout=30
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout as e:
            logger.error(f"API request timed out: {method} {endpoint}")
            logger.error(f"URL: {url}")
            logger.error(f"This might indicate:")
            logger.error("  1. Incorrect API base URL")
            logger.error("  2. Network connectivity issues")
            logger.error("  3. Server is down or unreachable")
            logger.error("  4. Firewall blocking the connection")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {method} {endpoint}")
            logger.error(f"URL: {url}")
            logger.error(f"Error: {str(e)}")
            logger.error("Please verify the API base URL is correct")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {method} {endpoint} - {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response: {e.response.text[:500]}")
            raise
    
    def get_server_time(self) -> Dict:
        """
        Get server time (public endpoint).
        
        Returns:
            Server time information
        """
        try:
            url = f"{self.base_url}/v3/serverTime"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Server time endpoint not found: {str(e)}, using local time")
            return {'timestamp': int(time.time() * 1000)}
    
    def get_exchange_info(self) -> Dict:
        """
        Get exchange information (public endpoint).
        
        Returns:
            Exchange information including trading pairs
        """
        try:
            url = f"{self.base_url}/v3/exchangeInfo"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Exchange info endpoint not found: {str(e)}")
            return {}
    
    def get_ticker(self, pair: Optional[str] = None) -> Dict:
        """
        Get market ticker information (public endpoint).
        
        Args:
            pair: Trading pair (e.g., 'BTC/USD'), optional
            
        Returns:
            Ticker data including price, volume, etc.
        """
        try:
            params = {'timestamp': int(time.time())}
            if pair:
                params['pair'] = pair
            
            response = self._make_request('GET', '/v3/ticker', params=params, use_milliseconds=False)
            logger.debug(f"Ticker retrieved for {pair}: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to get ticker for {pair}: {str(e)}")
            raise
    
    def get_balance(self) -> Dict:
        """
        Get account balance (SIGNED endpoint - uses GET not POST).
        
        Returns:
            Balance information
        """
        try:
            # According to demo code, balance uses GET with params and signature in headers
            params = {'timestamp': int(time.time() * 1000)}
            response = self._make_request('GET', '/v3/balance', params=params, use_milliseconds=True)
            logger.info(f"Balance retrieved: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to get balance: {str(e)}")
            raise
    
    def get_portfolio(self) -> Dict:
        """
        Get current portfolio information (uses balance endpoint).
        
        Returns:
            Portfolio data including balances
        """
        try:
            # Roostoo API uses balance endpoint for portfolio info
            balance = self.get_balance()
            return balance
        except Exception as e:
            logger.error(f"Failed to get portfolio: {str(e)}")
            raise
    
    def get_pending_order_count(self) -> Dict:
        """
        Get pending order count (SIGNED endpoint).
        
        Returns:
            Pending order count information
        """
        try:
            response = self._make_request('POST', '/v3/pending_order_count')
            logger.debug(f"Pending order count: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to get pending order count: {str(e)}")
            raise
    
    def place_order(self, pair: str, side: str, quantity: float, 
                   price: Optional[float] = None) -> Dict:
        """
        Place a trading order (SIGNED endpoint).
        
        Args:
            pair: Trading pair (e.g., 'BTC/USD')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            price: Price for limit orders (if None, creates MARKET order)
            
        Returns:
            Order response data
        """
        try:
            data = {
                'timestamp': int(time.time() * 1000),
                'pair': pair,
                'side': side.upper(),
                'quantity': str(quantity)
            }
            
            if price is not None:
                data['type'] = 'LIMIT'
                data['price'] = str(price)
            else:
                data['type'] = 'MARKET'
            
            response = self._make_request('POST', '/v3/place_order', data=data)
            logger.info(f"Order placed: {side} {quantity} {pair} - {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to place order: {str(e)}")
            raise
    
    def query_order(self, order_id: Optional[str] = None, pair: Optional[str] = None,
                   pending_only: Optional[bool] = None, offset: Optional[int] = None,
                   limit: Optional[int] = None) -> Dict:
        """
        Query orders (SIGNED endpoint).
        
        Args:
            order_id: Specific order ID (if provided, other params ignored)
            pair: Trading pair filter
            pending_only: Only return pending orders (True/False)
            offset: Offset for pagination
            limit: Limit number of results (default 100)
            
        Returns:
            Order information
        """
        try:
            data = {}
            
            if order_id:
                data['order_id'] = str(order_id)
            elif pair:
                data['pair'] = pair
                if pending_only is not None:
                    data['pending_only'] = 'TRUE' if pending_only else 'FALSE'
            
            if offset is not None:
                data['offset'] = str(offset)
            if limit is not None:
                data['limit'] = str(limit)
            
            response = self._make_request('POST', '/v3/query_order', data=data)
            logger.debug(f"Orders queried: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to query orders: {str(e)}")
            raise
    
    def cancel_order(self, order_id: Optional[str] = None, pair: Optional[str] = None) -> Dict:
        """
        Cancel order(s) (SIGNED endpoint).
        
        Args:
            order_id: Specific order ID to cancel
            pair: Cancel all pending orders for this pair
            If neither provided, cancels all pending orders
            
        Returns:
            Cancellation result
        """
        try:
            data = {}
            if order_id:
                data['order_id'] = str(order_id)
            elif pair:
                data['pair'] = pair
            
            response = self._make_request('POST', '/v3/cancel_order', data=data)
            logger.info(f"Order cancellation: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to cancel order: {str(e)}")
            raise
    
    def get_klines(self, pair: str, interval: str = '1m', limit: int = 100) -> List[Dict]:
        """
        Get candlestick/klines data for technical analysis.
        
        Note: This endpoint may not be in the public docs, but we'll try common patterns.
        If it doesn't exist, we can use ticker data or implement a workaround.
        
        Args:
            pair: Trading pair
            interval: Time interval (may not be supported)
            limit: Number of candles to retrieve
            
        Returns:
            List of kline data or empty list if endpoint not available
        """
        try:
            # Try to get ticker data as fallback
            ticker = self.get_ticker(pair)
            # Return ticker data in a format compatible with strategy
            # This is a workaround if klines endpoint doesn't exist
            logger.warning("Klines endpoint may not be available, using ticker data")
            return [ticker] if ticker else []
        except Exception as e:
            logger.error(f"Failed to get klines for {pair}: {str(e)}")
            return []
