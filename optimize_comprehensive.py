#!/usr/bin/env python3
"""
Comprehensive optimization script - tests multiple timeframes, rebalancing frequencies, and parameters.
"""
import yaml
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List
import json
import os

from backtest_advanced import run_backtest_advanced

logging.basicConfig(level=logging.WARNING)


class ComprehensiveOptimizer:
    """Comprehensive optimization across timeframes and parameters."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize optimizer."""
        with open(config_path, 'r') as f:
            self.base_config = yaml.safe_load(f)
    
    def create_test_config(self, params: Dict) -> Dict:
        """Create test configuration with modified parameters."""
        config = yaml.safe_load(yaml.dump(self.base_config))
        
        # Update parameters
        for key, value in params.items():
            if key == 'score_threshold':
                config['signals']['score_threshold'] = value
            elif key == 'top_k_normal':
                config['signals']['top_k_normal'] = value
            elif key == 'top_k_chop':
                config['signals']['top_k_chop'] = value
            elif key == 'cash_buffer_normal':
                config['sizing']['cash_buffer_normal'] = value
            elif key == 'hysteresis':
                config['signals']['hysteresis_weight_change'] = value
            elif key == 'cap_t1':
                config['sizing']['cap_t1'] = value
        
        return config
    
    def save_test_config(self, config: Dict, filename: str):
        """Save test configuration to file."""
        with open(filename, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    
    def optimize_timeframe(self, 
                          pairs: List[str],
                          config_params: Dict,
                          test_periods: List[Dict] = None,
                          random_seed: int = 42) -> pd.DataFrame:
        """
        Test strategy across multiple timeframes.
        
        Args:
            pairs: Trading pairs
            config_params: Configuration parameters to test
            test_periods: List of period dicts with 'months' or 'years'
            random_seed: Random seed
            
        Returns:
            DataFrame with results for each timeframe
        """
        if test_periods is None:
            test_periods = [
                {'months': 1, 'name': '1 Month'},
                {'months': 3, 'name': '3 Months'},
                {'months': 6, 'name': '6 Months'},
                {'years': 1, 'name': '1 Year'},
            ]
        
        # Create test config
        test_config = self.create_test_config(config_params)
        temp_config = "config/temp_timeframe_test.yaml"
        self.save_test_config(test_config, temp_config)
        
        results = []
        
        print(f"\n{'='*80}")
        print(f"TESTING ACROSS TIMEFRAMES")
        print(f"{'='*80}")
        print(f"Parameters: {config_params}")
        print(f"{'='*80}\n")
        
        for period in test_periods:
            period_name = period.get('name', f"{period.get('months', 0)}M/{period.get('years', 0)}Y")
            print(f"Testing: {period_name}...", end=" ")
            
            try:
                # Suppress output
                import sys
                from io import StringIO
                old_stdout = sys.stdout
                sys.stdout = StringIO()
                
                try:
                    result = run_backtest_advanced(
                        pairs=pairs,
                        months=period.get('months', 0),
                        years=period.get('years', 0),
                        config_path=temp_config,
                        random_seed=random_seed
                    )
                finally:
                    sys.stdout = old_stdout
                
                if result:
                    result_row = {
                        'timeframe': period_name,
                        **config_params,
                        'total_return_pct': result['total_return_pct'],
                        'sharpe_ratio': result['sharpe_ratio'],
                        'sortino_ratio': result['sortino_ratio'],
                        'calmar_ratio': result['calmar_ratio'],
                        'max_drawdown_pct': result['max_drawdown_pct'],
                        'total_trades': result['total_trades'],
                        'win_rate': result['win_rate'],
                        'total_fees': result.get('total_fees', 0),
                        'avg_profit_per_trade': result['avg_profit_per_trade'],
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
            # Calculate average metrics
            df['avg_sharpe'] = df['sharpe_ratio'].mean()
            df['avg_return'] = df['total_return_pct'].mean()
            df['avg_trades'] = df['total_trades'].mean()
            df['consistency_score'] = (df['sharpe_ratio'].std() < 1.0) * df['avg_sharpe']  # Prefer consistent
        
        return df
    
    def optimize_rebalancing_frequency(self,
                                      pairs: List[str],
                                      base_params: Dict,
                                      months: int = 1,
                                      random_seed: int = 42) -> pd.DataFrame:
        """
        Test different rebalancing frequencies.
        
        Note: This requires modifying the backtest code to support different frequencies.
        For now, we'll test different hysteresis values which affect effective frequency.
        """
        print(f"\n{'='*80}")
        print(f"TESTING REBALANCING FREQUENCY (via hysteresis)")
        print(f"{'='*80}\n")
        
        # Test different hysteresis values (affects how often we rebalance)
        hysteresis_values = [0.01, 0.02, 0.03, 0.05, 0.10]
        
        results = []
        
        for hyst in hysteresis_values:
            params = {**base_params, 'hysteresis': hyst}
            test_config = self.create_test_config(params)
            temp_config = f"config/temp_freq_{hyst}.yaml"
            self.save_test_config(test_config, temp_config)
            
            print(f"Testing hysteresis: {hyst} ({hyst*100:.1f}% threshold)...", end=" ")
            
            try:
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
                    result_row = {
                        'hysteresis': hyst,
                        **base_params,
                        'total_return_pct': result['total_return_pct'],
                        'sharpe_ratio': result['sharpe_ratio'],
                        'total_trades': result['total_trades'],
                        'total_fees': result.get('total_fees', 0),
                        'win_rate': result['win_rate'],
                    }
                    results.append(result_row)
                    
                    print(f"✅ Trades: {result['total_trades']}, "
                          f"Sharpe: {result['sharpe_ratio']:.3f}, "
                          f"Return: {result['total_return_pct']:.2f}%")
                else:
                    print("❌ Failed")
            
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
        
        df = pd.DataFrame(results)
        
        if len(df) > 0:
            # Calculate trade efficiency (return per trade)
            df['return_per_trade'] = df['total_return_pct'] / df['total_trades'].clip(lower=1)
            df['fee_cost_pct'] = (df['total_fees'] / 50000.0) * 100  # Fees as % of initial
        
        return df
    
    def full_optimization(self,
                         pairs: List[str] = None,
                         base_params: Dict = None,
                         random_seed: int = 42) -> Dict:
        """
        Run comprehensive optimization across all dimensions.
        
        Returns:
            Dictionary with optimization results
        """
        if pairs is None:
            pairs = ['BTC/USD', 'ETH/USD', 'SOL/USD', 'BNB/USD']
        
        if base_params is None:
            base_params = {
                'score_threshold': 0.02,
                'top_k_normal': 6,
                'cash_buffer_normal': 0.10,
                'hysteresis': 0.03,
            }
        
        print(f"\n{'='*80}")
        print(f"COMPREHENSIVE OPTIMIZATION")
        print(f"{'='*80}")
        print(f"Pairs: {pairs}")
        print(f"Base Parameters: {base_params}")
        print(f"{'='*80}\n")
        
        all_results = {}
        
        # Step 1: Test across timeframes with base params
        print("STEP 1: Testing across timeframes...")
        timeframe_results = self.optimize_timeframe(pairs, base_params, random_seed=random_seed)
        all_results['timeframe'] = timeframe_results
        
        # Step 2: Test rebalancing frequency
        print("\nSTEP 2: Testing rebalancing frequency...")
        freq_results = self.optimize_rebalancing_frequency(pairs, base_params, months=1, random_seed=random_seed)
        all_results['frequency'] = freq_results
        
        # Step 3: Parameter optimization (key parameters)
        print("\nSTEP 3: Testing parameter combinations...")
        param_results = self._optimize_parameters(pairs, months=1, random_seed=random_seed)
        all_results['parameters'] = param_results
        
        return all_results
    
    def _optimize_parameters(self, pairs: List[str], months: int = 1, random_seed: int = 42) -> pd.DataFrame:
        """Optimize key parameters."""
        param_ranges = {
            'score_threshold': [0.01, 0.02, 0.03],
            'top_k_normal': [4, 6, 8],
            'cash_buffer_normal': [0.05, 0.10, 0.15],
            'hysteresis': [0.02, 0.03, 0.05],
        }
        
        from itertools import product
        
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        all_combinations = list(product(*param_values))
        
        # Limit to 20 for speed
        if len(all_combinations) > 20:
            indices = np.linspace(0, len(all_combinations) - 1, 20, dtype=int)
            all_combinations = [all_combinations[i] for i in indices]
        
        results = []
        
        for i, combo in enumerate(all_combinations, 1):
            params = dict(zip(param_names, combo))
            test_config = self.create_test_config(params)
            temp_config = f"config/temp_param_{i}.yaml"
            self.save_test_config(test_config, temp_config)
            
            print(f"Test {i}/{len(all_combinations)}: {params}", end=" ... ")
            
            try:
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
                    result_row = {
                        **params,
                        'total_return_pct': result['total_return_pct'],
                        'sharpe_ratio': result['sharpe_ratio'],
                        'total_trades': result['total_trades'],
                        'win_rate': result['win_rate'],
                        'total_fees': result.get('total_fees', 0),
                    }
                    results.append(result_row)
                    print(f"✅ Sharpe: {result['sharpe_ratio']:.3f}, Return: {result['total_return_pct']:.2f}%")
                else:
                    print("❌")
            
            except Exception as e:
                print(f"❌ Error")
                continue
        
        df = pd.DataFrame(results)
        
        if len(df) > 0:
            # Calculate composite score
            df['sharpe_norm'] = (df['sharpe_ratio'] - df['sharpe_ratio'].min()) / (df['sharpe_ratio'].max() - df['sharpe_ratio'].min() + 1e-8)
            df['return_norm'] = (df['total_return_pct'] - df['total_return_pct'].min()) / (df['total_return_pct'].max() - df['total_return_pct'].min() + 1e-8)
            df['composite_score'] = 0.6 * df['sharpe_norm'] + 0.4 * df['return_norm']
            df = df.sort_values('composite_score', ascending=False)
        
        return df
    
    def print_summary(self, results: Dict):
        """Print optimization summary."""
        print(f"\n{'='*80}")
        print("OPTIMIZATION SUMMARY")
        print(f"{'='*80}\n")
        
        # Timeframe results
        if 'timeframe' in results and len(results['timeframe']) > 0:
            print("1. TIMEFRAME CONSISTENCY:")
            tf_df = results['timeframe']
            print(f"   Average Sharpe across timeframes: {tf_df['sharpe_ratio'].mean():.3f}")
            print(f"   Sharpe consistency (std): {tf_df['sharpe_ratio'].std():.3f}")
            print(f"   Average Return: {tf_df['total_return_pct'].mean():.2f}%")
            print(f"   Best timeframe: {tf_df.loc[tf_df['sharpe_ratio'].idxmax(), 'timeframe']}")
            print()
        
        # Frequency results
        if 'frequency' in results and len(results['frequency']) > 0:
            print("2. REBALANCING FREQUENCY:")
            freq_df = results['frequency']
            best_freq = freq_df.loc[freq_df['sharpe_ratio'].idxmax()]
            print(f"   Best hysteresis: {best_freq['hysteresis']:.3f} ({best_freq['hysteresis']*100:.1f}% threshold)")
            print(f"   Optimal trades: {best_freq['total_trades']:.0f}")
            print(f"   Sharpe at optimal: {best_freq['sharpe_ratio']:.3f}")
            print()
        
        # Parameter results
        if 'parameters' in results and len(results['parameters']) > 0:
            print("3. BEST PARAMETER CONFIGURATION:")
            param_df = results['parameters']
            best = param_df.iloc[0]
            print(f"   Score Threshold: {best['score_threshold']}")
            print(f"   Top K (Normal): {best['top_k_normal']}")
            print(f"   Cash Buffer: {best['cash_buffer_normal']}")
            print(f"   Hysteresis: {best['hysteresis']}")
            print(f"\n   Performance:")
            print(f"     Return: {best['total_return_pct']:.2f}%")
            print(f"     Sharpe: {best['sharpe_ratio']:.3f}")
            print(f"     Trades: {best['total_trades']:.0f}")
            print(f"     Win Rate: {best['win_rate']:.1f}%")
            print()
    
    def save_results(self, results: Dict, prefix: str = "optimization"):
        """Save all results to CSV files."""
        if 'timeframe' in results:
            results['timeframe'].to_csv(f"{prefix}_timeframe.csv", index=False)
            print(f"Saved: {prefix}_timeframe.csv")
        
        if 'frequency' in results:
            results['frequency'].to_csv(f"{prefix}_frequency.csv", index=False)
            print(f"Saved: {prefix}_frequency.csv")
        
        if 'parameters' in results:
            results['parameters'].to_csv(f"{prefix}_parameters.csv", index=False)
            print(f"Saved: {prefix}_parameters.csv")


def main():
    """Main optimization function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive backtest optimization')
    parser.add_argument('--pairs', nargs='+', default=['BTC/USD', 'ETH/USD', 'SOL/USD'],
                       help='Trading pairs')
    parser.add_argument('--quick', action='store_true', help='Quick optimization (fewer tests)')
    
    args = parser.parse_args()
    
    optimizer = ComprehensiveOptimizer()
    
    if args.quick:
        # Quick optimization
        print("Running QUICK optimization...")
        results = optimizer.full_optimization(
            pairs=args.pairs,
            base_params={
                'score_threshold': 0.02,
                'top_k_normal': 6,
                'cash_buffer_normal': 0.10,
                'hysteresis': 0.03,
            }
        )
    else:
        # Full optimization
        print("Running FULL optimization...")
        results = optimizer.full_optimization(pairs=args.pairs)
    
    optimizer.print_summary(results)
    optimizer.save_results(results)


if __name__ == "__main__":
    main()

