# Trading Mechanics - How $50k is Used

## Starting with $50,000

### Initial Allocation

**Starting Balance: $50,000**
- **Cash: $50,000** (100%)
- **Positions: $0** (0%)

## Cash Buffer Strategy

The bot keeps cash reserves based on market regime:

### Normal/Trend Market
- **Cash Buffer: 10%** = **$5,000** kept in cash
- **Available for Trading: 90%** = **$45,000**

### Chop Market (Sideways)
- **Cash Buffer: 20%** = **$10,000** kept in cash
- **Available for Trading: 80%** = **$40,000**

### Down Market (Bearish)
- **Cash Buffer: 60%** = **$30,000** kept in cash
- **Available for Trading: 40%** = **$20,000**

## Example: Trend Market (10% Cash Buffer)

### Step 1: Signal Generation
Bot finds 4 good signals:
- BTC/USD: score = 0.05 (strong)
- ETH/USD: score = 0.04
- SOL/USD: score = 0.03
- BNB/USD: score = 0.02

### Step 2: Position Sizing

**Available: $45,000** (90% of $50k)

**Inverse-volatility sizing:**
- Higher score + Lower volatility = Bigger position
- BTC: $15,000 (33% of available)
- ETH: $12,000 (27%)
- SOL: $10,000 (22%)
- BNB: $8,000 (18%)

**But wait - there are caps!**

### Step 3: Apply Tier Caps

**Tier 1 Assets** (BTC, ETH, SOL, BNB, etc.):
- **Max per position: 15%** of total equity = **$7,500**

**Tier 2 Assets** (ICP, SUI, DOT, etc.):
- **Max per position: 10%** of total equity = **$5,000**

**Tier 3 Assets** (BONK, PEPE, meme coins):
- **Max per position: 5%** of total equity = **$2,500**
- **Total Tier 3 sleeve: 12% max** = **$6,000**

### Step 4: Final Allocation

After caps:
- **BTC: $7,500** (15% - hit cap)
- **ETH: $7,500** (15% - hit cap)
- **SOL: $7,500** (15% - hit cap)
- **BNB: $7,500** (15% - hit cap)

**Total in positions: $30,000** (60%)
**Cash remaining: $20,000** (40%)

Wait, that's more than 10% cash buffer! Let me recalculate...

Actually, the cash buffer is applied **before** sizing, so:
- Target: 90% in positions = $45,000
- But caps limit individual positions
- Result: Might end up with more cash than buffer minimum

## How Buy/Sell Works

### Example: Buying BTC

**Current State:**
- Cash: $50,000
- Positions: None

**Signal: Buy BTC**
- Target weight: 15% of $50,000 = $7,500
- BTC price: $50,000
- Quantity: $7,500 / $50,000 = **0.15 BTC**

**Trade Execution:**
- Buy 0.15 BTC at $50,000
- Cost: $7,500
- New cash: $42,500
- New position: 0.15 BTC @ $50,000

### Example: Adding ETH

**Current State:**
- Cash: $42,500
- BTC: 0.15 @ $50,000 = $7,500
- Equity: $50,000

**Signal: Buy ETH**
- Target weight: 15% of $50,000 = $7,500
- ETH price: $3,000
- Quantity: $7,500 / $3,000 = **2.5 ETH**

**Trade Execution:**
- Buy 2.5 ETH at $3,000
- Cost: $7,500
- New cash: $35,000
- New positions:
  - BTC: 0.15 @ $50,000 = $7,500
  - ETH: 2.5 @ $3,000 = $7,500
- Total equity: $50,000

### Example: Rebalancing (Selling)

**Current State:**
- Cash: $35,000
- BTC: 0.15 @ $50,000 = $7,500 (now worth $8,000 - price went up!)
- ETH: 2.5 @ $3,000 = $7,500
- Equity: $50,500

**New Signal:**
- BTC score drops, target weight: 10% (down from 15%)
- SOL score rises, target weight: 15% (new)

**Rebalancing:**
1. **Reduce BTC:**
   - Current: $8,000 (15.8% of equity)
   - Target: 10% of $50,500 = $5,050
   - Sell: $8,000 - $5,050 = **$2,950 worth**
   - BTC price: $53,333 (went up)
   - Sell: $2,950 / $53,333 = **0.055 BTC**
   - Cash after: $35,000 + $2,950 = $37,950

2. **Buy SOL:**
   - Target: 15% of $50,500 = $7,575
   - SOL price: $100
   - Buy: $7,575 / $100 = **75.75 SOL**
   - Cost: $7,575
   - Cash after: $37,950 - $7,575 = $30,375

**Final State:**
- Cash: $30,375 (60% - higher due to BTC profit + caps)
- BTC: 0.095 @ $50,000 avg = $5,067
- ETH: 2.5 @ $3,000 = $7,500
- SOL: 75.75 @ $100 = $7,575
- Total equity: $50,517

## Minimum Order Size

**Minimum Order: $100**
- Small adjustments < $100 are skipped
- Prevents micro-trades and excessive fees

## Hysteresis (Prevents Churn)

**Weight change threshold: 3%**

If current position is 12% and target is 13%:
- Change: 1% < 3% threshold
- **Action: No trade** (saves fees)

If current position is 12% and target is 16%:
- Change: 4% > 3% threshold
- **Action: Trade** to rebalance

## Real Example from Backtest

**Starting: $50,000**
- Cash: $50,000
- Positions: 0

**After First Rebalance (Trend Market):**
- BTC: $7,500 (15%)
- ETH: $7,500 (15%)
- SOL: $7,500 (15%)
- BNB: $7,500 (15%)
- Cash: $20,000 (40%)

**Why 40% cash?**
- Caps limit positions to 15% each
- 4 positions × 15% = 60% in positions
- Remaining: 40% cash (higher than 10% buffer, which is fine)

## Summary

1. **Cash Buffer:**
   - Trend: 10% ($5,000)
   - Chop: 20% ($10,000)
   - Down: 60% ($30,000)

2. **Position Sizing:**
   - Inverse-volatility weighted
   - Tier 1: Max 15% per position
   - Tier 2: Max 10% per position
   - Tier 3: Max 5% per position

3. **Rebalancing:**
   - Every 30 minutes
   - Only if weight change > 3%
   - Minimum order: $100

4. **Result:**
   - Usually 60-80% in positions
   - 20-40% cash (often more than buffer due to caps)

The bot is **conservative** - it keeps cash reserves and limits position sizes to manage risk!

