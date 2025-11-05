# Available Trading Pairs on Roostoo

## Overview

Roostoo supports **80+ trading pairs**, all traded against **USD** (US Dollar). You start with **$50,000 USD** in your account.

## Current Bot Configuration

**Currently Trading**: `BTC/USD` (Bitcoin)

You can change this in `config.py` by modifying:
```python
TRADING_PAIR = 'BTC/USD'  # Change this to any pair below
```

## All Available Trading Pairs

### Major Cryptocurrencies (Recommended for Trading)
- **BTC/USD** - Bitcoin (Most liquid, stable)
- **ETH/USD** - Ethereum (Second largest, good liquidity)
- **BNB/USD** - Binance Coin
- **XRP/USD** - XRP
- **ADA/USD** - Cardano
- **SOL/USD** - Solana
- **DOGE/USD** - Dogecoin
- **AVAX/USD** - Avalanche
- **DOT/USD** - Polkadot
- **LINK/USD** - ChainLink
- **UNI/USD** - Uniswap
- **LTC/USD** - Litecoin
- **TON/USD** - Toncoin
- **NEAR/USD** - NEAR Protocol
- **APT/USD** - Aptos
- **SUI/USD** - Sui
- **TRX/USD** - TRON
- **XLM/USD** - Stellar
- **ZEC/USD** - Zcash
- **FIL/USD** - Filecoin
- **ICP/USD** - Internet Computer
- **HBAR/USD** - Hedera

### Meme Coins (Higher Volatility)
- **PEPE/USD** - Pepe
- **SHIB/USD** - SHIBA INU
- **FLOKI/USD** - FLOKI
- **BONK/USD** - BONK
- **DOGE/USD** - Dogecoin
- **WIF/USD** - Dogwifhat
- **PENGU/USD** - PENGU
- **TRUMP/USD** - TRUMP
- **1000CHEEMS/USD** - 1000CHEEMS

### DeFi & Other Tokens
- **AAVE/USD** - AAVE
- **CRV/USD** - Curve
- **PENDLE/USD** - Pendle
- **CAKE/USD** - PancakeSwap
- **ENA/USD** - Ethena
- **EIGEN/USD** - EigenLayer
- **ARB/USD** - Arbitrum
- **SEI/USD** - Sei
- **OMNI/USD** - OMNI
- **FET/USD** - Fetch.AI
- **ONDO/USD** - Ondo
- **WLD/USD** - Worldcoin
- **PAXG/USD** - PAX Gold
- **TAO/USD** - TAO
- **ZEN/USD** - Horizen

### Other Tokens
- **POL/USD** - Matic Network
- **WLFI/USD** - WLFI
- **XPL/USD** - XPL
- **OPEN/USD** - OPEN
- **HEMI/USD** - HEMI
- **AVNT/USD** - AVNT
- **ASTER/USD** - ASTER
- **LINEA/USD** - LINEA
- **VIRTUAL/USD** - VIRTUAL
- **BIO/USD** - BIO
- **LISTA/USD** - LISTA
- **FORM/USD** - FORM
- **TUT/USD** - TUT
- **MIRA/USD** - MIRA
- **PUMP/USD** - PUMP
- **PLUME/USD** - PLUME
- **EDEN/USD** - EDEN
- **S/USD** - S
- **BMT/USD** - BMT
- **SOMI/USD** - SOMI
- **STO/USD** - STO
- **CFX/USD** - Conflux

## Trading Pair Details

Each pair has specific trading parameters:
- **Price Precision**: How many decimal places for price
- **Amount Precision**: How many decimal places for quantity
- **MiniOrder**: Minimum order size (all are 1)

Example for BTC/USD:
- Price Precision: 2 (e.g., $101,344.39)
- Amount Precision: 5 (e.g., 0.12345 BTC)
- MiniOrder: 1

## Recommended Trading Pairs

### For Beginners (Lower Volatility)
1. **BTC/USD** - Bitcoin (Most stable, highest liquidity)
2. **ETH/USD** - Ethereum (Good liquidity, established)
3. **BNB/USD** - Binance Coin (Moderate volatility)

### For Experienced Traders (Higher Volatility)
1. **SOL/USD** - Solana
2. **AVAX/USD** - Avalanche
3. **DOGE/USD** - Dogecoin

### For High Risk/High Reward
1. **PEPE/USD** - Pepe (Very volatile)
2. **SHIB/USD** - SHIBA INU (Very volatile)
3. **BONK/USD** - BONK (Very volatile)

## How to Change Trading Pair

1. **Edit config.py**:
   ```python
   TRADING_PAIR = 'ETH/USD'  # Change from BTC/USD to ETH/USD
   ```

2. **Or use environment variable**:
   ```bash
   export TRADING_PAIR='ETH/USD'
   ```

3. **Restart the bot**:
   ```bash
   python main.py
   ```

## Current Price Example

From the API call, BTC/USD is currently trading at:
- **Last Price**: $101,344.40
- **Change**: -0.0548% (slight decrease)
- **Max Bid**: $101,344.39
- **Min Ask**: $101,344.40

## Strategy Considerations

Your moving average strategy works best with:
- **Liquid pairs** (high trading volume): BTC, ETH, BNB
- **Pairs with trends** (not just sideways): Avoid very stable coins
- **Pairs you understand**: Know the fundamentals

**Current Recommendation**: Stick with **BTC/USD** for testing, as it's the most liquid and stable.

