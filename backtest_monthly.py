#!/usr/bin/env python3
"""
Backtest strategy for each month (10th to end) from January to October 2025.
Each month starts fresh with $50,000.
"""
from backtest_advanced import run_backtest_advanced
import logging
import yaml
import pandas as pd
from datetime import datetime

logging.basicConfig(level=logging.WARNING)

def get_month_end(year, month):
    """Get last day of month."""
    if month == 12:
        return datetime(year + 1, 1, 1).replace(day=1) - pd.Timedelta(days=1)
    else:
        return datetime(year, month + 1, 1).replace(day=1) - pd.Timedelta(days=1)

def main():
    """Run backtests for each month."""
    
    # Load and update config with best parameters
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    config['signals']['score_threshold'] = 0.03
    config['signals']['top_k_normal'] = 8
    config['sizing']['cash_buffer_normal'] = 0.1
    config['signals']['hysteresis_weight_change'] = 0.05
    
    with open('config/temp_monthly_config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print("=" * 80)
    print("MONTHLY BACKTEST RESULTS (Jan-Oct 2025)")
    print("Each month starts fresh on 10th with $50,000")
    print("=" * 80)
    print()
    
    months = [
        ("January", 1),
        ("February", 2),
        ("March", 3),
        ("April", 4),
        ("May", 5),
        ("June", 6),
        ("July", 7),
        ("August", 8),
        ("September", 9),
        ("October", 10),
    ]
    
    results = []
    
    for month_name, month_num in months:
        year = 2025
        start_date = f"{year}-{month_num:02d}-10"
        end_date_obj = get_month_end(year, month_num)
        end_date = end_date_obj.strftime("%Y-%m-%d")
        
        print(f"Testing {month_name} 2025 ({start_date} to {end_date})...", end=" ")
        
        try:
            result = run_backtest_advanced(
                pairs=['BTC/USD', 'ETH/USD', 'SOL/USD', 'BNB/USD'],
                start_date=start_date,
                end_date=end_date,
                config_path='config/temp_monthly_config.yaml',
                random_seed=42,
                plot=False
            )
            
            if result:
                results.append({
                    'Month': month_name,
                    'Start Date': start_date,
                    'End Date': end_date,
                    'Initial Balance': result['initial_balance'],
                    'Final Balance': result['final_balance'],
                    'Total Return': result['total_return'],
                    'Return %': result['total_return_pct'],
                    'Sharpe Ratio': result['sharpe_ratio'],
                    'Sortino Ratio': result['sortino_ratio'],
                    'Max Drawdown %': result['max_drawdown_pct'],
                    'Total Trades': result['total_trades'],
                    'Win Rate %': result['win_rate'],
                    'Total Fees': result.get('total_fees', 0),
                    'Net Return (after fees)': result['total_return'] - result.get('total_fees', 0),
                })
                
                print(f"✅ Return: {result['total_return_pct']:.2f}%, "
                      f"Sharpe: {result['sharpe_ratio']:.3f}, "
                      f"Trades: {result['total_trades']}")
            else:
                print("❌ Failed")
                results.append({
                    'Month': month_name,
                    'Start Date': start_date,
                    'End Date': end_date,
                    'Initial Balance': 50000,
                    'Final Balance': 50000,
                    'Total Return': 0,
                    'Return %': 0,
                    'Sharpe Ratio': 0,
                    'Sortino Ratio': 0,
                    'Max Drawdown %': 0,
                    'Total Trades': 0,
                    'Win Rate %': 0,
                    'Total Fees': 0,
                    'Net Return (after fees)': 0,
                })
        
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                'Month': month_name,
                'Start Date': start_date,
                'End Date': end_date,
                'Initial Balance': 50000,
                'Final Balance': 50000,
                'Total Return': 0,
                'Return %': 0,
                'Sharpe Ratio': 0,
                'Sortino Ratio': 0,
                'Max Drawdown %': 0,
                'Total Trades': 0,
                'Win Rate %': 0,
                'Total Fees': 0,
                'Net Return (after fees)': 0,
            })
    
    # Create summary DataFrame
    df = pd.DataFrame(results)
    
    print()
    print("=" * 80)
    print("MONTHLY PERFORMANCE SUMMARY")
    print("=" * 80)
    print()
    
    # Print table
    print(f"{'Month':<12} {'Return %':<12} {'Sharpe':<10} {'Trades':<8} {'Fees':<10} {'Net Return':<12} {'Max DD %':<10}")
    print("-" * 80)
    
    for _, row in df.iterrows():
        print(f"{row['Month']:<12} {row['Return %']:>10.2f}%  {row['Sharpe Ratio']:>8.3f}  "
              f"{int(row['Total Trades']):>6}  ${row['Total Fees']:>8.2f}  "
              f"${row['Net Return (after fees)']:>10,.2f}  {row['Max Drawdown %']:>8.2f}%")
    
    print()
    print("=" * 80)
    print("AGGREGATE STATISTICS")
    print("=" * 80)
    print(f"Average Return:        {df['Return %'].mean():.2f}%")
    print(f"Average Sharpe:         {df['Sharpe Ratio'].mean():.3f}")
    print(f"Average Trades/Month:   {df['Total Trades'].mean():.1f}")
    print(f"Average Fees/Month:    ${df['Total Fees'].mean():.2f}")
    print(f"Total Fees (all months): ${df['Total Fees'].sum():.2f}")
    print(f"Total Return (all months): ${df['Total Return'].sum():,.2f}")
    print(f"Total Net Return:      ${df['Net Return (after fees)'].sum():,.2f}")
    print()
    print(f"Best Month:            {df.loc[df['Return %'].idxmax(), 'Month']} ({df['Return %'].max():.2f}%)")
    print(f"Worst Month:           {df.loc[df['Return %'].idxmin(), 'Month']} ({df['Return %'].min():.2f}%)")
    print(f"Best Sharpe:           {df.loc[df['Sharpe Ratio'].idxmax(), 'Month']} ({df['Sharpe Ratio'].max():.3f})")
    print()
    
    # Save to CSV
    df.to_csv('monthly_backtest_results.csv', index=False)
    print("=" * 80)
    print(f"Results saved to: monthly_backtest_results.csv")
    print("=" * 80)
    
    return df

if __name__ == "__main__":
    main()

