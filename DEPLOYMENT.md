# Deployment Guide

This guide provides step-by-step instructions for deploying the trading bot on AWS EC2.

## Prerequisites

- AWS account with EC2 access
- SSH key pair for EC2 access
- Basic knowledge of Linux command line

## Step 1: Launch EC2 Instance

1. **Log into AWS Console**
   - Navigate to EC2 service
   - Click "Launch Instance"

2. **Choose Instance Configuration**:
   - **Name**: `crypto-trading-bot`
   - **AMI**: Ubuntu Server 22.04 LTS (free tier eligible)
   - **Instance Type**: t2.micro or t3.small (t2.micro is sufficient for testing)
   - **Key Pair**: Select or create a new key pair for SSH access
   - **Network Settings**: 
     - Allow SSH (port 22) from your IP
     - No need for HTTP/HTTPS ports (bot uses outbound API calls only)
   - **Storage**: 8 GB (default is sufficient)

3. **Launch Instance**

## Step 2: Connect to EC2 Instance

```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

## Step 3: Install Dependencies

```bash
# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
sudo apt-get install -y docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify Docker installation
docker --version
docker-compose --version
```

## Step 4: Install Git and Clone Repository

```bash
# Install Git
sudo apt-get install -y git

# Clone your repository
git clone <your-repo-url>
cd crypto_algo_bot

# Or if you need to upload files manually:
# Use scp or create files directly on the server
```

## Step 5: Configure Environment Variables

```bash
# Create .env file
nano .env
```

Add the following content:
```
ROOSTOO_API_KEY=Qqaqe0nsBMoPzhRvusONKFh5kARjTSkoG9zxG0HVuXQcnBGPmuWMXjRxBTXhe30o
ROOSTOO_API_SECRET=CTaBKUVDOZCwxrQCMeAXFMWxpDFXsHmS0qfnNjvlO7IPBc57jV5cVXqFX3zj6qv6
ROOSTOO_BASE_URL=https://api.roostoo.com
LOG_LEVEL=INFO
```

Save and exit (Ctrl+X, then Y, then Enter).

## Step 6: Test Connection (Optional)

Before running the bot, test the API connection:

```bash
# Build Docker image
docker build -t crypto-trading-bot .

# Run connection test
docker run --rm --env-file .env crypto-trading-bot python test_connection.py
```

## Step 7: Start the Bot

### Option A: Using Docker Compose (Recommended)

```bash
# Start the bot in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Option B: Using Docker Directly

```bash
# Build image
docker build -t crypto-trading-bot .

# Run container
docker run -d \
  --name crypto-trading-bot \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/trading_bot.log:/app/trading_bot.log \
  crypto-trading-bot
```

## Step 8: Monitor the Bot

```bash
# View real-time logs
docker-compose logs -f trading-bot

# Or for direct Docker
docker logs -f crypto-trading-bot

# Check container status
docker ps

# View log file
tail -f trading_bot.log
```

## Step 9: Manage the Bot

### Stop the Bot
```bash
docker-compose down
# Or
docker stop crypto-trading-bot
```

### Restart the Bot
```bash
docker-compose restart
# Or
docker restart crypto-trading-bot
```

### Update the Bot
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

## Step 10: Set Up Auto-Start (Optional)

Create a systemd service for automatic startup:

```bash
sudo nano /etc/systemd/system/trading-bot.service
```

Add the following content:
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
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

Check status:
```bash
sudo systemctl status trading-bot
```

## Troubleshooting

### Bot Won't Start
1. Check Docker is running: `sudo systemctl status docker`
2. Check logs: `docker-compose logs`
3. Verify .env file exists and has correct credentials
4. Test API connection: `python test_connection.py`

### API Connection Errors
1. Verify API credentials in .env
2. Check network connectivity: `ping api.roostoo.com`
3. Verify API base URL is correct
4. Check system time is synchronized: `date`

### Container Issues
1. Check container logs: `docker logs crypto-trading-bot`
2. Restart container: `docker-compose restart`
3. Rebuild if code changed: `docker-compose build`

### Resource Usage
Monitor resource usage:
```bash
# CPU and Memory
docker stats

# Disk space
df -h
```

## Security Best Practices

1. **Never commit .env file** - It's in .gitignore
2. **Use IAM roles** - For production, use AWS IAM roles instead of storing credentials
3. **Limit SSH access** - Only allow SSH from trusted IPs
4. **Regular updates** - Keep system and Docker updated
5. **Monitor logs** - Regularly check for suspicious activity

## Cost Optimization

- Use t2.micro or t3.small instances (free tier eligible)
- Stop instance when not testing (to save costs)
- Use spot instances for testing (cheaper but can be interrupted)
- Monitor AWS costs in Cost Explorer

## Next Steps

1. Monitor bot performance and adjust strategy parameters
2. Review logs regularly for any issues
3. Adjust trading parameters in `config.py` based on performance
4. Consider adding monitoring/alerting (CloudWatch, etc.)

## Support

For issues or questions:
1. Check logs first: `docker-compose logs`
2. Test API connection: `python test_connection.py`
3. Review README.md for configuration options
4. Check Roostoo API documentation for endpoint details

