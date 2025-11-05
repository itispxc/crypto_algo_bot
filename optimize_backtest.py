#!/usr/bin/env python3
"""
Backtest optimization script.
Tests different parameter combinations to find optimal settings for Sharpe ratio and profit.
"""
import yaml
import json
import pandas as pd
from itertools import product
from datetime import datetime, timedelta
import logging
from typing import Dict, List
import numpy as np

from backtest_advanced import run_backtest_advanced

logging.basicConfig(level=logging.WARNING)  # Suppress detailed logs during optimization


class BacktestOptimizer:
    """Optimize backtest parameters for best Sharpe ratio and profit."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize optimizer."""
        with open(config_path, 'r') as f:
            self.base_config = yaml.safe_load(f)
    
    def create_test_config(self, params: Dict) -> Dict:
        """
        Create test configuration with modified parameters.
        
        Args:
            params: Dictionary of parameters to modify
            
        Returns:
            Modified config dictionary
        """
        config = yaml.safe_load(yaml.dump(self.base_config))  # Deep copy
        
        # Update parameters
        if 'score_threshold' in params:
            config['signals']['score_threshold'] = params['score_threshold']
        
        if 'top_k_normal' in params:
            config['signals']['top_k_normal'] = params['top_k_normal']
        
        if 'top_k_chop' in params:
            config['signals']['top_k_chop'] = params['top_k_chop']
        
        if 'top_k_down' in params:
            config['signals']['top_k_down'] = params['top_k_down']
        
        if 'cash_buffer_normal' in params:
            config['sizing']['cash_buffer_normal'] = params['cash_buffer_normal']
        
        if 'cash_buffer_chop' in params:
            config['sizing']['cash_buffer_chop'] = params['cash_buffer_chop']
        
        if 'hysteresis' in params:
            config['signals']['hysteresis_weight_change'] = params['hysteresis']
        
        if 'cap_t1' in params:
            config['sizing']['cap_t1'] = params['cap_t1']
        
        return config
    
    def save_test_config(self, config: Dict, filename: str):
        """Save test configuration to file."""
        with open(filename, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    
    def run_optimization(self, 
                        pairs: List[str] = None,
                        months: int = 1,
                        param_ranges: Dict = None,
                        max_tests: int = 50,
                        random_seed: int = 42) -> pd.DataFrame:
        """
        Run optimization over parameter ranges.
        
        Args:
            pairs: Trading pairs to test
            months: Number of months for backtest
            param_ranges: Dictionary of parameter ranges to test
            max_tests: Maximum number of tests to run
            random_seed: Random seed for reproducibility
            
        Returns:
            DataFrame with results for all configurations
        """
        if pairs is None:
            pairs = ['BTC/USD', 'ETH/USD', 'SOL/USD', 'BNB/USD', 'DOGE/USD']
        
        if param_ranges is None:
            # Default parameter ranges to test
            param_ranges = {
                'score_threshold': [0.01, 0.02, 0.03, 0.05],
                'top_k_normal': [4, 6, 8, 10],
                'cash_buffer_normal': [0.05, 0.10, 0.15, 0.20],
                'hysteresis': [0.02, 0.03, 0.05],
            }
        
        # Generate all combinations
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        
        all_combinations = list(product(*param_values))
        
        # Limit to max_tests
        if len(all_combinations) > max_tests:
            print(f"⚠️  {len(all_combinations)} combinations found, limiting to {max_tests}")
            # Use stratified sampling
            indices = np.linspace(0, len(all_combinations) - 1, max_tests, dtype=int)
            all_combinations = [all_combinations[i] for i in indices]
        
        print(f"\n{'='*80}")
        print(f"OPTIMIZATION RUN")
        print(f"{'='*80}")
        print(f"Pairs: {pairs}")
        print(f"Period: {months} month(s)")
        print(f"Total tests: {len(all_combinations)}")
        print(f"{'='*80}\n")
        
        results = []
        
        for i, combo in enumerate(all_combinations, 1):
            params = dict(zip(param_names, combo))
            
            # Create test config
            test_config = self.create_test_config(params)
            
            # Save to temp file
            temp_config = f"config/temp_optimize_{i}.yaml"
            self.save_test_config(test_config, temp_config)
            
            try:
                print(f"Test {i}/{len(all_combinations)}: {params}", end=" ... ")
                
                # Run backtest (suppress output)
                import sys
                from io import StringIO
                old_stdout = sys.stdout
                sys.stdout = StringIO()
                
                try:
                    result = run_backtest_advanced(
                        pairs=pairs,
                        months=months,
                        config_path=temp_config,
                        random_seed=random_seed
                    )
                finally:
                    sys.stdout = old_stdout
                
                if result:
                    # Store results
                    result_row = {
                        'test_num': i,
                        **params,
                        'total_return_pct': result['total_return_pct'],
                        'total_return': result['total_return'],
                        'sharpe_ratio': result['sharpe_ratio'],
                        'sortino_ratio': result['sortino_ratio'],
                        'calmar_ratio': result['calmar_ratio'],
                        'max_drawdown_pct': result['max_drawdown_pct'],
                        'total_trades': result['total_trades'],
                        'win_rate': result['win_rate'],
                        'avg_profit_per_trade': result['avg_profit_per_trade'],
                        'final_balance': result['final_balance'],
                    }
                    results.append(result_row)
                    
                    print(f"  ✅ Return: {result['total_return_pct']:.2f}%, "
                          f"Sharpe: {result['sharpe_ratio']:.3f}, "
                          f"Trades: {result['total_trades']}")
                else:
                    print(f"  ❌ Failed")
            
            except Exception as e:
                print(f"  ❌ Error: {e}")
                continue
        
        # Create DataFrame
        df = pd.DataFrame(results)
        
        # Calculate composite score (Sharpe-weighted return)
        if len(df) > 0:
            # Normalize metrics
            df['sharpe_norm'] = (df['sharpe_ratio'] - df['sharpe_ratio'].min()) / (df['sharpe_ratio'].max() - df['sharpe_ratio'].min() + 1e-8)
            df['return_norm'] = (df['total_return_pct'] - df['total_return_pct'].min()) / (df['total_return_pct'].max() - df['total_return_pct'].min() + 1e-8)
            df['composite_score'] = 0.6 * df['sharpe_norm'] + 0.4 * df['return_norm']
            
            # Sort by composite score
            df = df.sort_values('composite_score', ascending=False)
        
        return df
    
    def print_results(self, df: pd.DataFrame, top_n: int = 10):
        """Print top results."""
        if len(df) == 0:
            print("No results to display")
            return
        
        print(f"\n{'='*80}")
        print(f"OPTIMIZATION RESULTS - Top {top_n}")
        print(f"{'='*80}\n")
        
        # Display top results
        top_results = df.head(top_n)
        
        for idx, row in top_results.iterrows():
            print(f"Rank {top_results.index.get_loc(idx) + 1}:")
            print(f"  Parameters:")
            param_cols = [c for c in row.index if c not in ['test_num', 'total_return_pct', 'total_return', 
                                                             'sharpe_ratio', 'sortino_ratio', 'calmar_ratio',
                                                             'max_drawdown_pct', 'total_trades', 'win_rate',
                                                             'avg_profit_per_trade', 'final_balance',
                                                             'sharpe_norm', 'return_norm', 'composite_score']]
            for col in param_cols:
                if col in row:
                    print(f"    {col}: {row[col]}")
            print(f"  Performance:")
            print(f"    Return: {row['total_return_pct']:.2f}%")
            print(f"    Sharpe: {row['sharpe_ratio']:.3f}")
            print(f"    Sortino: {row['sortino_ratio']:.3f}")
            print(f"    Max DD: {row['max_drawdown_pct']:.2f}%")
            print(f"    Trades: {row['total_trades']}")
            print(f"    Win Rate: {row['win_rate']:.1f}%")
            print(f"    Composite Score: {row['composite_score']:.3f}")
            print()
    
    def save_results(self, df: pd.DataFrame, filename: str = "optimization_results.csv"):
        """Save results to CSV."""
        df.to_csv(filename, index=False)
        print(f"Results saved to {filename}")


def main():
    """Main optimization function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Optimize backtest parameters')
    parser.add_argument('--pairs', nargs='+', default=['BTC/USD', 'ETH/USD', 'SOL/USD'],
                       help='Trading pairs to test')
    parser.add_argument('--months', type=int, default=1, help='Number of months')
    parser.add_argument('--max-tests', type=int, default=30, help='Maximum number of tests')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    optimizer = BacktestOptimizer()
    
    # Define parameter ranges to test
    param_ranges = {
        'score_threshold': [0.01, 0.02, 0.03],  # Signal quality filter
        'top_k_normal': [4, 6, 8],  # Number of positions in trend
        'cash_buffer_normal': [0.05, 0.10, 0.15],  # Cash reserve
        'hysteresis': [0.02, 0.03, 0.05],  # Rebalance threshold
    }
    
    # Run optimization
    results_df = optimizer.run_optimization(
        pairs=args.pairs,
        months=args.months,
        param_ranges=param_ranges,
        max_tests=args.max_tests,
        random_seed=args.seed
    )
    
    # Print results
    optimizer.print_results(results_df, top_n=10)
    
    # Save results
    optimizer.save_results(results_df)
    
    # Print summary statistics
    if len(results_df) > 0:
        print(f"\n{'='*80}")
        print("SUMMARY STATISTICS")
        print(f"{'='*80}")
        print(f"Best Sharpe Ratio: {results_df['sharpe_ratio'].max():.3f}")
        print(f"Best Return: {results_df['total_return_pct'].max():.2f}%")
        print(f"Best Composite Score: {results_df['composite_score'].max():.3f}")
        print(f"Average Trades: {results_df['total_trades'].mean():.1f}")
        print(f"Median Trades: {results_df['total_trades'].median():.1f}")
        print(f"{'='*80}\n")
        
        # Show best configuration
        best = results_df.iloc[0]
        print("🏆 BEST CONFIGURATION:")
        print(f"  Score Threshold: {best.get('score_threshold', 'N/A')}")
        print(f"  Top K (Normal): {best.get('top_k_normal', 'N/A')}")
        print(f"  Cash Buffer: {best.get('cash_buffer_normal', 'N/A')}")
        print(f"  Hysteresis: {best.get('hysteresis', 'N/A')}")
        print(f"\n  Performance:")
        print(f"    Return: {best['total_return_pct']:.2f}%")
        print(f"    Sharpe: {best['sharpe_ratio']:.3f}")
        print(f"    Trades: {best['total_trades']}")
        print(f"    Win Rate: {best['win_rate']:.1f}%")


if __name__ == "__main__":
    main()

