"""
Quick script to check current prices of popular trading pairs.
"""
from roostoo_client import RoostooClient
from config import Config

config = Config()
client = RoostooClient(
    api_key=config.ROOSTOO_API_KEY,
    api_secret=config.ROOSTOO_API_SECRET,
    base_url=config.ROOSTOO_BASE_URL
)

# Get a few popular tickers
pairs = ['BTC/USD', 'ETH/USD', 'BNB/USD', 'SOL/USD', 'DOGE/USD']
print('Current Prices on Roostoo:')
print('=' * 60)
for pair in pairs:
    try:
        ticker = client.get_ticker(pair)
        if ticker.get('Success') and 'Data' in ticker:
            data = ticker['Data'].get(pair, {})
            price = data.get('LastPrice', 'N/A')
            change = data.get('Change', 0)
            print(f'{pair:12} | Price: ${price:>15} | Change: {change:>7.2f}%')
    except Exception as e:
        print(f'{pair:12} | Error: {str(e)[:50]}')

