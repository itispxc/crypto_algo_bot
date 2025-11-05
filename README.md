# Crypto Trading Bot

An autonomous trading bot for the Roostoo mock exchange that makes buy, hold, and sell decisions using a moving average crossover strategy.

## Features

- **Autonomous Trading**: Makes trading decisions without human intervention
- **Moving Average Strategy**: Uses fast and slow moving average crossovers for entry/exit signals
- **Risk Management**: Position sizing and stop-loss/take-profit parameters
- **Real-time Data**: Fetches live market data from Roostoo API
- **Portfolio Management**: Monitors and manages portfolio positions
- **Comprehensive Logging**: Detailed logs for monitoring and debugging

## Strategy

The bot uses a **Simple Moving Average (SMA) Crossover Strategy**:

- **Buy Signal**: Fast MA crosses above Slow MA (bullish crossover)
- **Sell Signal**: Fast MA crosses below Slow MA (bearish crossover)
- **Hold**: No crossover detected, maintain current position

### Default Parameters
- Fast MA Period: 10
- Slow MA Period: 30
- Trading Interval: 60 seconds
- Max Position Size: 10% of portfolio
- Minimum Order Size: 0.001

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
