# Quick Start Guide

Get your trading bot running in 5 minutes!

## Prerequisites

- Python 3.11+ installed
- Roostoo API credentials (provided in hackathon resources)

## Option 1: Local Python Setup (Fastest)

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set environment variables**:
```bash
export ROOSTOO_API_KEY="Qqaqe0nsBMoPzhRvusONKFh5kARjTSkoG9zxG0HVuXQcnBGPmuWMXjRxBTXhe30o"
export ROOSTOO_API_SECRET="CTaBKUVDOZCwxrQCMeAXFMWxpDFXsHmS0qfnNjvlO7IPBc57jV5cVXqFX3zj6qv6"
```

3. **Test connection** (optional):
```bash
python test_connection.py
```

4. **Run the bot**:
```bash
python main.py
```

## Option 2: Using the Startup Script

1. **Make script executable** (already done):
```bash
chmod +x run.sh
```

2. **Run the script**:
```bash
./run.sh
```

The script will:
- Create virtual environment
- Install dependencies
- Optionally test API connection
- Start the bot

## Option 3: Docker (Recommended for Deployment)

1. **Build Docker image**:
```bash
docker build -t crypto-trading-bot .
```

2. **Create .env file**:
```bash
cat > .env << EOF
ROOSTOO_API_KEY=Qqaqe0nsBMoPzhRvusONKFh5kARjTSkoG9zxG0HVuXQcnBGPmuWMXjRxBTXhe30o
ROOSTOO_API_SECRET=CTaBKUVDOZCwxrQCMeAXFMWxpDFXsHmS0qfnNjvlO7IPBc57jV5cVXqFX3zj6qv6
ROOSTOO_BASE_URL=https://api.roostoo.com
LOG_LEVEL=INFO
EOF
```

3. **Run with Docker Compose**:
```bash
docker-compose up -d
```

4. **View logs**:
```bash
docker-compose logs -f
```

## What to Expect

Once running, the bot will:

1. **Connect to Roostoo API** - Authenticate and verify connection
2. **Fetch portfolio data** - Get current balance and positions
3. **Get market data** - Retrieve candlestick data for analysis
4. **Generate signals** - Use moving average strategy to determine buy/sell/hold
5. **Execute trades** - Place orders when signals are generated
6. **Log everything** - Detailed logs in console and `trading_bot.log`

## Monitor the Bot

### View Logs
```bash
# Python
tail -f trading_bot.log

# Docker
docker-compose logs -f
```

### Check Status
```bash
# Docker
docker-compose ps
docker stats
```

## Stop the Bot

- **Python**: Press `Ctrl+C`
- **Docker**: `docker-compose down`
- **Docker (direct)**: `docker stop crypto-trading-bot`

## Customization

Edit `config.py` to adjust:
- Trading pair: `TRADING_PAIR = 'BTC/USDT'`
- Strategy periods: `FAST_MA_PERIOD = 10`, `SLOW_MA_PERIOD = 30`
- Trading interval: `TRADING_INTERVAL = 60` (seconds)
- Position sizing: `MAX_POSITION_SIZE = 0.1` (10% of portfolio)

## Troubleshooting

### "API connection failed"
- Verify API credentials are correct
- Check network connectivity
- Ensure API base URL is correct
- Review Roostoo API documentation for endpoint paths

### "Insufficient data"
- Bot needs at least 30 candles (slow MA period)
- Wait for more data or reduce `SLOW_MA_PERIOD` in config

### "Insufficient balance"
- Check account balance on Roostoo
- Reduce `MAX_POSITION_SIZE` in config
- Ensure you have enough balance for minimum order size

## Next Steps

1. **Test thoroughly** - Start with small amounts
2. **Monitor performance** - Review logs and trading results
3. **Adjust strategy** - Tune parameters based on market conditions
4. **Deploy to EC2** - Follow `DEPLOYMENT.md` for AWS deployment

## Support

- Check `README.md` for detailed documentation
- Review `DEPLOYMENT.md` for AWS EC2 setup
- Check logs for detailed error messages
- Verify Roostoo API documentation for endpoint details

Happy trading! 🚀

