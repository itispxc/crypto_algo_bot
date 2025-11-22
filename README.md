# Crypto Trading Bot

An autonomous trading bot for the Roostoo mock exchange that makes buy, hold, and sell decisions using a moving average crossover strategy.

## Features

- **Autonomous Trading**: Makes trading decisions without human intervention
- **Moving Average Strategy**: Uses fast and slow moving average crossovers for entry/exit signals
- **Risk Management**: Position sizing and stop-loss/take-profit parameters
- **Real-time Data**: Fetches live market data from Roostoo API
- **Portfolio Management**: Monitors and manages portfolio positions
- **Comprehensive Logging**: Detailed logs for monitoring and debugging

## Strategy Documentation

### Core Strategy: Support/Resistance Breakout (S/R Breakout)

The bot implements a **Support/Resistance Breakout Strategy** for ZEC/USD trading on 1-minute timeframes. The core idea is to identify key price levels (support and resistance) and enter long positions when price breaks above resistance with volume confirmation.

#### Core Concept

1. **Pivot Point Detection**: The strategy identifies pivot highs (resistance levels) by scanning price action over a rolling window. A pivot high is a local maximum where the high price is the highest within a defined left and right bar window.

2. **Breakout Entry**: When price breaks above a detected resistance level with:
   - **Trend confirmation**: Price must be above the 200-period EMA (uptrend filter)
   - **Volume confirmation**: Volume oscillator exceeds threshold OR price is above 20-period EMA
   - **Cooldown period**: Minimum time between trades to avoid overtrading

3. **Profit Target Exit**: Positions are closed when profit reaches 4.2%, ensuring consistent profit-taking.

#### Implementation Details

- **Data Source**: Historical OHLCV data from Binance API (1-minute candles)
- **Indicators**:
  - 200-period EMA (trend filter)
  - 20-period EMA (momentum confirmation)
  - Volume Oscillator (5 EMA vs 10 EMA of volume)
  - Pivot High/Low detection (6 bars left, 9 bars right)
- **Entry Conditions**: Price breaks above pivot high resistance + trend + volume confirmation
- **Exit Conditions**: Fixed profit target of 4.2%
- **Risk Management**: 21-bar cooldown between trades, long-only (no short selling)

#### Strategy Parameters

- `left_bars`: 6 (pivot detection window - left side)
- `right_bars`: 9 (pivot detection window - right side)
- `volume_threshold`: 31.0 (minimum volume oscillator for entry)
- `cooldown_bars`: 21 (minutes between trades)
- `profit_target`: 4.2% (take profit level)

#### Note on BTC Position

The bot maintains a BTC/USD position that was added initially to establish a position on the leaderboard before switching to the S/R breakout strategy. BTC is automatically sold when its price reaches $95,950, after which the bot focuses exclusively on ZEC/USD trading.

## Installation

### Prerequisites
- Python 3.11+
- Roostoo API credentials

### Local Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd crypto_algo_bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API credentials
```

Or set environment variables directly:
```bash
export ROOSTOO_API_KEY="your_api_key"
export ROOSTOO_API_SECRET="your_api_secret"
```

4. Run the bot:
```bash
python main.py
```

## Docker Deployment

### Build and Run with Docker

1. Build the Docker image:
```bash
docker build -t crypto-trading-bot .
```

2. Run the container:
```bash
docker run -d \
  --name crypto-trading-bot \
  -e ROOSTOO_API_KEY="your_api_key" \
  -e ROOSTOO_API_SECRET="your_api_secret" \
  -e ROOSTOO_BASE_URL="https://api.roostoo.com" \
  crypto-trading-bot
```

### Using Docker Compose

1. Create a `.env` file with your credentials:
```
ROOSTOO_API_KEY=your_api_key
ROOSTOO_API_SECRET=your_api_secret
ROOSTOO_BASE_URL=https://api.roostoo.com
```

2. Start the bot:
```bash
docker-compose up -d
```

3. View logs:
```bash
docker-compose logs -f
```

## AWS EC2 Deployment

### Setup Steps

1. **Launch EC2 Instance**:
   - Choose Ubuntu 22.04 LTS
   - Instance type: t2.micro or t3.small (sufficient for bot)
   - Configure security group (SSH access)

2. **Connect to EC2**:
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

3. **Install Docker**:
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker $USER
newgrp docker
```

4. **Clone and Setup**:
```bash
git clone <repository-url>
cd crypto_algo_bot
```

5. **Configure Environment**:
```bash
nano .env
# Add your API credentials
```

6. **Run with Docker Compose**:
```bash
docker-compose up -d
```

7. **Monitor Logs**:
```bash
docker-compose logs -f trading-bot
```

### Running as a Service (Optional)

Create a systemd service for auto-start:

```bash
sudo nano /etc/systemd/system/trading-bot.service
```

Add:
```ini
[Unit]
Description=Crypto Trading Bot
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/crypto_algo_bot
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
User=ubuntu

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

## Configuration

Edit `config.py` to customize:

- Trading pair (default: BTC/USDT)
- Moving average periods
- Trading interval
- Position sizing
- Risk management parameters

## API Endpoints Used

The bot interfaces with Roostoo API:

- `GET /api/v1/portfolio` - Get portfolio information
- `GET /api/v1/balance` - Get account balance
- `GET /api/v1/ticker` - Get ticker data
- `GET /api/v1/klines` - Get candlestick data
- `POST /api/v1/order` - Place trading orders

## Logging

Logs are written to:
- Console (stdout)
- File: `trading_bot.log`

Log levels can be configured via `LOG_LEVEL` environment variable (DEBUG, INFO, WARNING, ERROR).

## Risk Management

- **Position Sizing**: Maximum 10% of portfolio per trade
- **Minimum Order Size**: Prevents dust trades
- **Stop Loss**: 2% (configurable)
- **Take Profit**: 5% (configurable)

## Monitoring

Monitor the bot:

1. **Check logs**:
```bash
tail -f trading_bot.log
```

2. **Docker logs**:
```bash
docker-compose logs -f
```

3. **Check status**:
```bash
docker-compose ps
```

## Troubleshooting

### API Authentication Errors
- Verify API credentials are correct
- Check API key permissions
- Ensure system time is synchronized

### Insufficient Data
- Bot requires at least 30 candles (slow MA period)
- Check API connection and data availability

### Trading Errors
- Verify sufficient balance
- Check minimum order size requirements
- Ensure trading pair is valid

## Development

### Project Structure

```
crypto_algo_bot/
├── main.py              # Entry point
├── trading_bot.py       # Main bot orchestrator
├── roostoo_client.py    # API client
├── strategy.py          # Trading strategies
├── config.py            # Configuration
├── requirements.txt     # Dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose config
└── README.md           # This file
```

## License

Open source - available for hackathon validation.

## Disclaimer

This bot is for educational and hackathon purposes. Trading involves risk. Use at your own discretion.
