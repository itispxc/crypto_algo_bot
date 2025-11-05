#!/bin/bash

# Trading Bot Startup Script

echo "=========================================="
echo "Crypto Trading Bot - Startup Script"
echo "=========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Creating from example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Please edit .env with your API credentials"
    else
        echo "Error: .env.example not found"
        exit 1
    fi
fi

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Test connection (optional)
read -p "Do you want to test API connection first? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Testing API connection..."
    python test_connection.py
    if [ $? -ne 0 ]; then
        echo "Connection test failed. Please check your credentials."
        exit 1
    fi
fi

# Start the bot
echo "Starting trading bot..."
echo "Press Ctrl+C to stop"
python main.py

