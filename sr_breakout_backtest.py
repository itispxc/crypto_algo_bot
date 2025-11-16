"""
Run the refined S/R breakout strategy backtest and simple ML-based parameter search.
"""
from __future__ import annotations

import argparse
import json
import os
import random
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import yaml
from sklearn.ensemble import RandomForestRegressor

from src.data_client import DataClient
from src.strategies.sr_breakout import SRBreakoutBacktester, SRBreakoutParams


def candles_to_df(candles):
    return pd.DataFrame(
        [
            {
                "timestamp": c.ts,
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume,
            }
            for c in candles
        ]
    )


def fetch_candles(client: DataClient, pair: str, interval: str, hours: int):
    limit = min(hours + 10, 1000)
    candles = client.get_candles(pair, interval, limit)
    if not candles:
        raise RuntimeError("No candles returned.")
    df = candles_to_df(candles)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    df = df[df["timestamp"] >= int(cutoff.timestamp() * 1000)]
    return df


def random_params() -> SRBreakoutParams:
    return SRBreakoutParams(
        left_bars=random.randint(8, 24),
        right_bars=random.randint(8, 24),
        volume_threshold=random.uniform(10, 40),
        stop_multiplier=round(random.uniform(1.1, 1.9), 2),
        tp_atr_multiple=round(random.uniform(1.2, 2.8), 2),
        trail_atr_offset=round(random.uniform(1.0, 2.2), 2),
        cooldown_bars=random.randint(4, 18),
    )


def main():
    parser = argparse.ArgumentParser(description="SR breakout backtest + ML tuning")
    parser.add_argument("--pair", default="BTC/USD")
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--hours", type=int, default=72)
    parser.add_argument("--trials", type=int, default=40)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)

    data_client = DataClient(config)
    df = fetch_candles(data_client, args.pair, args.interval, args.hours)
    fee_bps = config["exchange"]["fee_bps"]
    backtester = SRBreakoutBacktester(df, fee_bps=fee_bps)

    base_params = SRBreakoutParams()
    base_result = backtester.run(base_params)
    print("=== Base Parameter Backtest ===")
    print(json.dumps(base_result, indent=2, default=str))

    param_vectors = []
    returns = []
    param_records = []

    for _ in range(args.trials):
        params = random_params()
        result = backtester.run(params)
        param_vectors.append(params.as_vector())
        returns.append(result["total_return_pct"])
        param_records.append((params, result))

    model = RandomForestRegressor(n_estimators=200, random_state=args.seed)
    model.fit(param_vectors, returns)

    best_idx = int(np.argmax(returns))
    best_params, best_result = param_records[best_idx]

    print("\n=== Random Search Top Result ===")
    print(json.dumps(best_result, indent=2, default=str))

    feature_importance = model.feature_importances_
    feature_names = [
        "left_bars",
        "right_bars",
        "volume_threshold",
        "stop_multiplier",
        "tp_atr_multiple",
        "trail_atr_offset",
        "cooldown_bars",
    ]
    print("\nFeature importances:")
    for name, imp in sorted(zip(feature_names, feature_importance), key=lambda x: -x[1]):
        print(f"  {name}: {imp:.3f}")


if __name__ == "__main__":
    main()


