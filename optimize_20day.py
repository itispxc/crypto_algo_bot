#!/usr/bin/env python3
"""
Optimize strategy for 20-day competition period.
Tests random 20-day windows and finds optimal trade count for highest Sharpe and profit.
"""
import yaml
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List
from itertools import product

from backtest_advanced import run_backtest_advanced

logging.basicConfig(level=logging.WARNING)


class Optimizer20Day:
    """Optimize for 20-day competition period."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize optimizer."""
        with open(config_path, 'r') as f:
            self.base_config = yaml.safe_load(f)
    
    def create_test_config(self, params: Dict) -> Dict:
        """Create test configuration."""
        config = yaml.safe_load(yaml.dump(self.base_config))
        
        for key, value in params.items():
            if key == 'score_threshold':
                config['signals']['score_threshold'] = value
            elif key == 'top_k_normal':
                config['signals']['top_k_normal'] = value
            elif key == 'cash_buffer_normal':
                config['sizing']['cash_buffer_normal'] = value
            elif key == 'hysteresis':
                config['signals']['hysteresis_weight_change'] = value
        
        return config
    
    def save_test_config(self, config: Dict, filename: str):
        """Save test configuration."""
        with open(filename, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    
    def test_random_20day_periods(self,
                                  pairs: List[str],
                                  config_params: Dict,
                                  num_periods: int = 5,
                                  random_seed: int = 42) -> pd.DataFrame:
        """
        Test strategy on multiple random 20-day periods.
        
        Args:
            pairs: Trading pairs
            config_params: Configuration parameters
            num_periods: Number of random 20-day periods to test
            random_seed: Random seed
            
        Returns:
            DataFrame with results for each period
        """
        np.random.seed(random_seed)
        
        # Generate random 20-day periods in the past
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)  # Look back 60 days for periods
        
        results = []
        
        print(f"\n{'='*80}")
        print(f"TESTING RANDOM 20-DAY PERIODS")
        print(f"{'='*80}")
        print(f"Parameters: {config_params}")
        print(f"Testing {num_periods} random 20-day periods...")
        print(f"{'='*80}\n")
        
        # Create test config
        test_config = self.create_test_config(config_params)
        temp_config = "config/temp_20day_test.yaml"
        self.save_test_config(test_config, temp_config)
        
        # Generate unique random periods
        used_periods = set()
        for i in range(num_periods):
            # Random start date (ensuring we can fit 20 days)
            # Pick a random number between 20 and 60 days ago
            max_attempts = 100
            for attempt in range(max_attempts):
                period_start_days_ago = np.random.randint(20, 60)  # Random days ago (20-60 days)
                period_start = end_date - timedelta(days=period_start_days_ago)
                period_end = period_start + timedelta(days=20)
                period_key = (period_start.date(), period_end.date())
                if period_key not in used_periods:
                    used_periods.add(period_key)
                    break
            else:
                # Fallback: use sequential periods if we can't generate unique ones
                period_start = end_date - timedelta(days=60 + i * 5)
                period_end = period_start + timedelta(days=20)
            
            period_name = f"{period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"
            
            print(f"Period {i+1}/{num_periods}: {period_name}...", end=" ")
            
            try:
                # Suppress output and logging
                import sys
                import logging
                from io import StringIO
                old_stdout = sys.stdout
                sys.stdout = StringIO()
                
                # Temporarily set logging to ERROR level
                old_level = logging.getLogger().level
                logging.getLogger().setLevel(logging.ERROR)
                
                try:
                    result = run_backtest_advanced(
                        pairs=pairs,
                        start_date=period_start.strftime("%Y-%m-%d"),
                        end_date=period_end.strftime("%Y-%m-%d"),
                        config_path=temp_config,
                        random_seed=random_seed,
                        plot=False  # Skip plotting during optimization
                    )
                finally:
                    sys.stdout = old_stdout
                    logging.getLogger().setLevel(old_level)
                
                if result:
                    result_row = {
                        'period': period_name,
                        'period_num': i + 1,
                        **config_params,
                        'total_return_pct': result['total_return_pct'],
                        'sharpe_ratio': result['sharpe_ratio'],
                        'sortino_ratio': result['sortino_ratio'],
                        'max_drawdown_pct': result['max_drawdown_pct'],
                        'total_trades': result['total_trades'],
                        'win_rate': result['win_rate'],
                        'total_fees': result.get('total_fees', 0),
                        'avg_profit_per_trade': result['avg_profit_per_trade'],
                        'final_balance': result['final_balance'],
                    }
                    results.append(result_row)
                    
                    print(f"✅ Return: {result['total_return_pct']:.2f}%, "
                          f"Sharpe: {result['sharpe_ratio']:.3f}, "
                          f"Trades: {result['total_trades']}")
                else:
                    print("❌ Failed")
            
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
        
        df = pd.DataFrame(results)
        
        if len(df) > 0:
            # Calculate aggregate statistics
            df['avg_sharpe'] = df['sharpe_ratio'].mean()
            df['avg_return'] = df['total_return_pct'].mean()
            df['avg_trades'] = df['total_trades'].mean()
            df['sharpe_std'] = df['sharpe_ratio'].std()
            df['return_std'] = df['total_return_pct'].std()
            
            # Composite score: Sharpe consistency + average return
            df['consistency'] = 1.0 / (1.0 + df['sharpe_std'])  # Higher is better
            df['composite_score'] = 0.5 * df['avg_sharpe'] + 0.3 * df['avg_return'] + 0.2 * df['consistency']
        
        return df
    
    def optimize_trade_count(self,
                            pairs: List[str],
                            num_periods: int = 5,
                            random_seed: int = 42) -> pd.DataFrame:
        """
        Find optimal trade count for 20-day periods.
        Tests different parameter combinations to find best trade frequency.
        
        Returns:
            DataFrame with results ranked by composite score
        """
        print(f"\n{'='*80}")
        print(f"OPTIMIZING FOR 20-DAY COMPETITION")
        print(f"{'='*80}\n")
        
        # Test different parameter combinations
        # Focus on parameters that affect trade count
        param_ranges = {
            'score_threshold': [0.01, 0.015, 0.02, 0.03],  # Signal quality
            'top_k_normal': [4, 6, 8],  # Number of positions
            'cash_buffer_normal': [0.05, 0.10, 0.15],  # Cash reserve
            'hysteresis': [0.02, 0.03, 0.05, 0.10],  # Rebalance frequency
        }
        
        # Generate combinations
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        all_combinations = list(product(*param_values))
        
        # Limit to 30 for reasonable runtime
        if len(all_combinations) > 30:
            indices = np.linspace(0, len(all_combinations) - 1, 30, dtype=int)
            all_combinations = [all_combinations[i] for i in indices]
        
        print(f"Testing {len(all_combinations)} parameter combinations...")
        print(f"Each tested on {num_periods} random 20-day periods\n")
        
        all_results = []
        
        for i, combo in enumerate(all_combinations, 1):
            params = dict(zip(param_names, combo))
            
            print(f"Test {i}/{len(all_combinations)}: {params}")
            
            # Test on multiple random periods
            period_results = self.test_random_20day_periods(
                pairs=pairs,
                config_params=params,
                num_periods=num_periods,
                random_seed=random_seed
            )
            
            if len(period_results) > 0:
                # Aggregate results across periods
                agg_result = {
                    **params,
                    'avg_sharpe': period_results['sharpe_ratio'].mean(),
                    'std_sharpe': period_results['sharpe_ratio'].std(),
                    'avg_return': period_results['total_return_pct'].mean(),
                    'std_return': period_results['total_return_pct'].std(),
                    'avg_trades': period_results['total_trades'].mean(),
                    'min_trades': period_results['total_trades'].min(),
                    'max_trades': period_results['total_trades'].max(),
                    'avg_win_rate': period_results['win_rate'].mean(),
                    'avg_fees': period_results['total_fees'].mean(),
                    'consistency_score': 1.0 / (1.0 + period_results['sharpe_ratio'].std()),
                    'num_periods_tested': len(period_results),
                }
                
                # Composite score for ranking
                agg_result['composite_score'] = (
                    0.5 * agg_result['avg_sharpe'] +
                    0.3 * (agg_result['avg_return'] / 10.0) +  # Normalize return
                    0.2 * agg_result['consistency_score']
                )
                
                all_results.append(agg_result)
                
                print(f"  → Avg Sharpe: {agg_result['avg_sharpe']:.3f}, "
                      f"Avg Return: {agg_result['avg_return']:.2f}%, "
                      f"Avg Trades: {agg_result['avg_trades']:.1f}")
                print()
        
        df = pd.DataFrame(all_results)
        
        if len(df) > 0:
            # Sort by composite score
            df = df.sort_values('composite_score', ascending=False)
        
        return df
    
    def print_results(self, df: pd.DataFrame, top_n: int = 10):
        """Print top results."""
        if len(df) == 0:
            print("No results to display")
            return
        
        print(f"\n{'='*80}")
        print(f"TOP {top_n} CONFIGURATIONS FOR 20-DAY COMPETITION")
        print(f"{'='*80}\n")
        
        top_results = df.head(top_n)
        
        for idx, (_, row) in enumerate(top_results.iterrows(), 1):
            print(f"Rank {idx}:")
            print(f"  Parameters:")
            print(f"    Score Threshold: {row['score_threshold']}")
            print(f"    Top K (Normal): {row['top_k_normal']}")
            print(f"    Cash Buffer: {row['cash_buffer_normal']}")
            print(f"    Hysteresis: {row['hysteresis']}")
            print(f"  Performance (avg across {row['num_periods_tested']} periods):")
            print(f"    Avg Sharpe: {row['avg_sharpe']:.3f} (std: {row['std_sharpe']:.3f})")
            print(f"    Avg Return: {row['avg_return']:.2f}% (std: {row['std_return']:.2f}%)")
            print(f"    Avg Trades: {row['avg_trades']:.1f} (range: {row['min_trades']:.0f}-{row['max_trades']:.0f})")
            print(f"    Avg Win Rate: {row['avg_win_rate']:.1f}%")
            print(f"    Avg Fees: ${row['avg_fees']:.2f}")
            print(f"    Consistency Score: {row['consistency_score']:.3f}")
            print(f"    Composite Score: {row['composite_score']:.4f}")
            print()
    
    def print_trade_count_analysis(self, df: pd.DataFrame):
        """Analyze optimal trade count."""
        if len(df) == 0:
            return
        
        print(f"\n{'='*80}")
        print("TRADE COUNT ANALYSIS")
        print(f"{'='*80}\n")
        
        # Group by trade count ranges
        df['trade_range'] = pd.cut(df['avg_trades'], 
                                  bins=[0, 5, 10, 15, 20, 30, 100],
                                  labels=['0-5', '5-10', '10-15', '15-20', '20-30', '30+'])
        
        summary = df.groupby('trade_range').agg({
            'avg_sharpe': 'mean',
            'avg_return': 'mean',
            'composite_score': 'mean',
            'avg_trades': 'mean'
        }).sort_values('composite_score', ascending=False)
        
        print("Performance by Trade Count Range:")
        print()
        for trade_range, row in summary.iterrows():
            print(f"  {trade_range} trades:")
            print(f"    Avg Sharpe: {row['avg_sharpe']:.3f}")
            print(f"    Avg Return: {row['avg_return']:.2f}%")
            print(f"    Avg Trades: {row['avg_trades']:.1f}")
            print()
        
        # Find optimal range
        best_range = summary.index[0]
        print(f"🏆 Optimal Trade Count Range: {best_range}")
        print(f"   This range gives best composite score")


def main():
    """Main optimization function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Optimize for 20-day competition')
    parser.add_argument('--pairs', nargs='+', 
                       default=['BTC/USD', 'ETH/USD', 'SOL/USD', 'BNB/USD'],
                       help='Trading pairs')
    parser.add_argument('--periods', type=int, default=5,
                       help='Number of random 20-day periods to test')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed')
    
    args = parser.parse_args()
    
    optimizer = Optimizer20Day()
    
    # Run optimization
    results_df = optimizer.optimize_trade_count(
        pairs=args.pairs,
        num_periods=args.periods,
        random_seed=args.seed
    )
    
    # Print results
    optimizer.print_results(results_df, top_n=10)
    optimizer.print_trade_count_analysis(results_df)
    
    # Save results
    results_df.to_csv("optimization_20day_results.csv", index=False)
    print(f"\n{'='*80}")
    print(f"Results saved to: optimization_20day_results.csv")
    print(f"{'='*80}\n")
    
    # Show best configuration
    if len(results_df) > 0:
        best = results_df.iloc[0]
        print("🏆 BEST CONFIGURATION FOR 20-DAY COMPETITION:")
        print(f"\nUpdate config/config.yaml with:")
        print(f"  signals:")
        print(f"    score_threshold: {best['score_threshold']}")
        print(f"    top_k_normal: {int(best['top_k_normal'])}")
        print(f"    hysteresis_weight_change: {best['hysteresis']}")
        print(f"  sizing:")
        print(f"    cash_buffer_normal: {best['cash_buffer_normal']}")
        print(f"\nExpected performance:")
        print(f"  Avg Sharpe: {best['avg_sharpe']:.3f}")
        print(f"  Avg Return: {best['avg_return']:.2f}%")
        print(f"  Avg Trades: {best['avg_trades']:.1f} per 20 days")
        print(f"  Avg Win Rate: {best['avg_win_rate']:.1f}%")
        print()


if __name__ == "__main__":
    main()

