"""
Run S/R Breakout Strategy Live
"""
import yaml
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.sr_breakout_live import run_sr_breakout_live

if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    run_sr_breakout_live(config)

