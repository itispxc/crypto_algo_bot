#!/usr/bin/env python3
"""
Diagnostic script to verify Sharpe ratio calculation.
"""
import numpy as np
import pandas as pd
from backtest_advanced import run_backtest_advanced
import logging
import yaml

logging.basicConfig(level=logging.WARNING)

def analyze_sharpe_calculation():
    """Run a backtest and analyze the Sharpe calculation in detail."""
    
    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    config['signals']['score_threshold'] = 0.03
    config['signals']['top_k_normal'] = 8
    config['sizing']['cash_buffer_normal'] = 0.1
    config['signals']['hysteresis_weight_change'] = 0.05
    
    with open('config/temp_sharpe_config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print("Running backtest for January 2025 (10th to 31st)...")
    print("=" * 80)
    
    result = run_backtest_advanced(
        pairs=['BTC/USD', 'ETH/USD', 'SOL/USD', 'BNB/USD'],
        start_date='2025-01-10',
        end_date='2025-01-31',
        config_path='config/temp_sharpe_config.yaml',
        random_seed=42,
        plot=False
    )
    
    if not result:
        print("Backtest failed!")
        return
    
    # Extract equity curve
    equity_df = result['equity_curve']
    equity_values = equity_df['equity'].values
    
    # Calculate returns (per 30-minute period) - for comparison
    returns = np.diff(equity_values) / equity_values[:-1]
    returns = returns[~np.isnan(returns)]
    
    # Calculate daily returns (what we actually use now)
    equity_daily = equity_df.resample('D').last()
    equity_daily_values = equity_daily['equity'].values
    daily_returns = np.diff(equity_daily_values) / equity_daily_values[:-1]
    daily_returns = daily_returns[~np.isnan(daily_returns)]
    
    # Calculate statistics for both
    mean_return_30m = np.mean(returns)
    std_return_30m = np.std(returns)
    mean_return_daily = np.mean(daily_returns)
    std_return_daily = np.std(daily_returns)
    
    # Annualization factors
    periods_per_year_30m = 252 * 48
    annualization_factor_30m = np.sqrt(periods_per_year_30m)
    annualization_factor_daily = np.sqrt(252)
    
    # Sharpe calculations (old vs new)
    sharpe_old_30m = (mean_return_30m / std_return_30m) * annualization_factor_30m if std_return_30m > 0 else 0
    sharpe_new_daily = (mean_return_daily / std_return_daily) * annualization_factor_daily if std_return_daily > 0 else 0
    
    # Annualized statistics
    annual_mean_daily = mean_return_daily * 252
    annual_std_daily = std_return_daily * annualization_factor_daily
    
    # Print detailed analysis
    print("\n" + "=" * 80)
    print("SHARPE RATIO DIAGNOSTICS")
    print("=" * 80)
    print(f"\nEquity Curve Statistics:")
    print(f"  Initial Balance: ${equity_values[0]:,.2f}")
    print(f"  Final Balance:   ${equity_values[-1]:,.2f}")
    print(f"  Total Return:   {(equity_values[-1] / equity_values[0] - 1) * 100:.2f}%")
    print(f"  Number of 30-min periods: {len(returns)}")
    print(f"  Number of daily periods: {len(daily_returns)}")
    print(f"  Periods per year (30-min): {periods_per_year_30m:,}")
    print(f"  Annualization factor (30-min): {annualization_factor_30m:.2f}")
    print(f"  Annualization factor (daily): {annualization_factor_daily:.2f}")
    
    print(f"\nReturn Statistics (per 30-minute period - OLD METHOD):")
    print(f"  Mean return:     {mean_return_30m:.8f} ({mean_return_30m * 100:.6f}%)")
    print(f"  Std dev:         {std_return_30m:.8f} ({std_return_30m * 100:.6f}%)")
    print(f"  Min return:     {np.min(returns):.8f} ({np.min(returns) * 100:.6f}%)")
    print(f"  Max return:      {np.max(returns):.8f} ({np.max(returns) * 100:.6f}%)")
    
    # Count negative returns
    negative_returns = returns[returns < 0]
    zero_returns = np.sum(np.abs(returns) < 1e-8)
    print(f"  Negative returns: {len(negative_returns)} / {len(returns)} ({len(negative_returns)/len(returns)*100:.1f}%)")
    print(f"  Zero returns:     {zero_returns} / {len(returns)} ({zero_returns/len(returns)*100:.1f}%)")
    print(f"  ⚠️  PROBLEM: {zero_returns/len(returns)*100:.1f}% of periods have zero returns!")
    print(f"     This inflates Sharpe when using 30-min bars because std is artificially low.")
    
    print(f"\nReturn Statistics (per DAY - NEW METHOD):")
    print(f"  Mean return:     {mean_return_daily:.8f} ({mean_return_daily * 100:.6f}%)")
    print(f"  Std dev:         {std_return_daily:.8f} ({std_return_daily * 100:.6f}%)")
    print(f"  Min return:     {np.min(daily_returns):.8f} ({np.min(daily_returns) * 100:.6f}%)")
    print(f"  Max return:      {np.max(daily_returns):.8f} ({np.max(daily_returns) * 100:.6f}%)")
    
    negative_daily = daily_returns[daily_returns < 0]
    print(f"  Negative returns: {len(negative_daily)} / {len(daily_returns)} ({len(negative_daily)/len(daily_returns)*100:.1f}%)")
    
    # Annualized statistics
    print(f"\nAnnualized Statistics (Daily Method):")
    print(f"  Annualized mean:  {annual_mean_daily:.6f} ({annual_mean_daily * 100:.2f}%)")
    print(f"  Annualized std:   {annual_std_daily:.6f} ({annual_std_daily * 100:.2f}%)")
    
    print(f"\nSharpe Ratio Calculations:")
    print(f"  OLD (30-min bars): {sharpe_old_30m:.3f} ⚠️  INFLATED due to many zero-return periods")
    print(f"  NEW (daily bars):  {sharpe_new_daily:.3f} ✓ More realistic")
    print(f"  Reported:          {result['sharpe_ratio']:.3f}")
    
    # Verify they match
    if abs(sharpe_new_daily - result['sharpe_ratio']) < 0.1:
        print(f"  ✓ Calculation matches!")
    else:
        print(f"  ✗ Calculation mismatch!")
    
    # Check if Sharpe is realistic
    print(f"\n" + "=" * 80)
    print("REALITY CHECK")
    print("=" * 80)
    
    # For context, typical Sharpe ratios:
    # - 0-1: Poor
    # - 1-2: OK
    # - 2-3: Good
    # - 3-4: Very good
    # - >4: Exceptional (rare)
    # - >30: Likely an error or unrealistic
    
    if sharpe_new_daily > 30:
        print(f"  ⚠️  WARNING: Sharpe ratio of {sharpe_new_daily:.2f} is extremely high!")
        print(f"     This suggests:")
        print(f"     1. Very low volatility (std={std_return_daily:.8f} per day)")
        print(f"     2. Very consistent returns (mean={mean_return_daily:.8f} per day)")
        print(f"     3. Possible calculation issue or unrealistic backtest conditions")
        print(f"\n     Typical Sharpe ratios:")
        print(f"     - 0-1: Poor")
        print(f"     - 1-2: OK")
        print(f"     - 2-3: Good")
        print(f"     - 3-4: Very good")
        print(f"     - >4: Exceptional (rare)")
        print(f"     - >30: Likely unrealistic or calculation error")
    else:
        print(f"  ✓ Sharpe ratio of {sharpe_new_daily:.2f} is within reasonable range")
    
    # Show return distribution
    print(f"\n" + "=" * 80)
    print("RETURN DISTRIBUTION ANALYSIS")
    print("=" * 80)
    print(f"\nReturn Percentiles (per 30-minute period):")
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    for p in percentiles:
        val = np.percentile(returns, p)
        print(f"  {p:2d}th percentile: {val:+.8f} ({val*100:+.6f}%)")
    
    # Check if there are many zero returns (equity not changing)
    zero_returns = np.sum(np.abs(returns) < 1e-8)
    print(f"\n  Returns close to zero (<1e-8): {zero_returns} / {len(returns)} ({zero_returns/len(returns)*100:.1f}%)")
    
    if zero_returns > len(returns) * 0.5:
        print(f"  ⚠️  WARNING: More than 50% of returns are essentially zero!")
        print(f"     This means the equity curve is flat for many periods,")
        print(f"     which can artificially inflate the Sharpe ratio.")
    
    return {
        'mean_return_30m': mean_return_30m,
        'std_return_30m': std_return_30m,
        'mean_return_daily': mean_return_daily,
        'std_return_daily': std_return_daily,
        'sharpe_old': sharpe_old_30m,
        'sharpe_new': sharpe_new_daily,
        'periods_30m': len(returns),
        'periods_daily': len(daily_returns),
        'zero_returns': zero_returns
    }

if __name__ == "__main__":
    analyze_sharpe_calculation()

