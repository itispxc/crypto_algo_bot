# Fees in the Trading Algorithm

## ✅ Fees ARE Now Accounted For!

I've fixed the backtest to properly account for fees on every trade.

## How Fees Work

### Fee Rate
- **Config**: `fee_bps: 10` (10 basis points = 0.1%)
- **Per Trade**: 0.1% on buy AND 0.1% on sell
- **Round Trip**: 0.2% total (0.1% + 0.1%)

### Example: Buying $7,500 of BTC

**Without Fees (Old Bug):**
- Cost: $7,500
- Cash after: $42,500

**With Fees (Fixed):**
- Cost: $7,500
- Fee: $7,500 × 0.001 = **$7.50**
- Total cost: $7,507.50
- Cash after: $42,492.50

### Example: Selling $7,500 of BTC

**Without Fees (Old Bug):**
- Revenue: $7,500
- Cash after: $50,000

**With Fees (Fixed):**
- Revenue: $7,500
- Fee: $7,500 × 0.001 = **$7.50**
- Net revenue: $7,492.50
- Cash after: $49,992.50

## Where Fees Are Accounted

### 1. Signal Scoring (Already Working)
```python
# In alpha_model.py
fees = 2 * (fee_bps / 10000.0)  # Round trip
exp_net = score - (fees + slippage)
```
- Filters out trades that won't be profitable after fees
- Only signals with `exp_ret_net > threshold` are considered

### 2. Trade Execution (Now Fixed!)
```python
# Buy: Deduct cost + fee
fee = cost * fee_rate
total_cost = cost + fee
self.cash -= total_cost  # Deduct both

# Sell: Add revenue - fee
fee = revenue * fee_rate
net_revenue = revenue - fee
self.cash += net_revenue  # Add net (after fee)
```

### 3. Profit Calculation (Now Fixed!)
```python
# Profit = (sell_price - entry_price) * qty - fees
profit = (price - entry_price) * sell_qty - fee
```

## Impact on Backtest Results

### Before Fix:
- Fees not deducted from cash
- Profits calculated without fees
- Results were **overly optimistic**

### After Fix:
- Fees deducted on every buy
- Fees deducted on every sell
- Profits calculated after fees
- Results are **realistic**

### Example Impact:
If you made 10 round-trip trades of $7,500 each:
- **Old**: No fees deducted
- **New**: $7.50 × 2 × 10 = **$150 in fees deducted**

On $50,000 portfolio:
- **Old return**: Might show 15%
- **New return**: Might show 14.7% (after fees)

## Fee Configuration

Edit `config/config.yaml`:
```yaml
exchange:
  fee_bps: 10  # 0.1% per trade (10 basis points)
```

Common fee rates:
- **Maker**: 0.05-0.1% (10 bps)
- **Taker**: 0.1-0.2% (10-20 bps)
- **VIP**: 0.02-0.05% (2-5 bps)

## Verifying Fees

Check the backtest results:
```python
results = run_backtest_advanced(...)
print(f"Total fees: ${results['total_fees']:.2f}")
```

Or check individual trades:
```python
for trade in results['trades']:
    if trade.get('fee'):
        print(f"{trade['action']} {trade['pair']}: fee=${trade['fee']:.2f}")
```

## Summary

✅ **Fees ARE accounted for** in:
1. Signal scoring (filters unprofitable trades)
2. Trade execution (deducted from cash)
3. Profit calculation (net of fees)
4. Results display (shows total fees paid)

The backtest now gives **realistic results** that account for trading costs! 💰

