"""
Support/Resistance breakout strategy implementation for hourly data.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class SRBreakoutParams:
    """Strategy hyper-parameters."""

    left_bars: int = 12
    right_bars: int = 12
    volume_threshold: float = 15.0
    stop_multiplier: float = 1.4
    tp_atr_multiple: float = 1.8
    trail_atr_offset: float = 1.3
    cooldown_bars: int = 6

    def as_vector(self) -> List[float]:
        return [
            self.left_bars,
            self.right_bars,
            self.volume_threshold,
            self.stop_multiplier,
            self.tp_atr_multiple,
            self.trail_atr_offset,
            self.cooldown_bars,
        ]


class SRBreakoutBacktester:
    """
    Vectorized backtester for the S/R breakout strategy.
    """

    def __init__(self, candles: pd.DataFrame, fee_bps: float = 10.0):
        if candles.empty:
            raise ValueError("Candles dataframe is empty")

        self.df = candles.copy().reset_index(drop=True)
        self.df["timestamp"] = pd.to_datetime(self.df["timestamp"], unit="ms")
        self.fee_rate = fee_bps / 10_000.0
        self._prepare_indicators()

    def _prepare_indicators(self):
        df = self.df
        df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()
        df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
        vol = df["volume"]
        df["vol_ema5"] = vol.ewm(span=5, adjust=False).mean()
        df["vol_ema10"] = vol.ewm(span=10, adjust=False).mean()
        df["atr14"] = self._atr(df, period=14)

    @staticmethod
    def _atr(df: pd.DataFrame, period: int) -> pd.Series:
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift(1)).abs()
        low_close = (df["low"] - df["close"].shift(1)).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.ewm(alpha=1 / period, adjust=False).mean()

    @staticmethod
    @staticmethod
    def _pivot_high(series: pd.Series, left: int, right: int) -> pd.Series:
        arr = series.values
        piv = np.full(len(series), np.nan)
        for i in range(left, len(series) - right):
            window = arr[i - left : i + right + 1]
            if arr[i] == np.max(window):
                piv[i + right] = arr[i]
        return pd.Series(piv, index=series.index)

    @staticmethod
    def _pivot_low(series: pd.Series, left: int, right: int) -> pd.Series:
        arr = series.values
        piv = np.full(len(series), np.nan)
        for i in range(left, len(series) - right):
            window = arr[i - left : i + right + 1]
            if arr[i] == np.min(window):
                piv[i + right] = arr[i]
        return pd.Series(piv, index=series.index)

    def run(self, params: SRBreakoutParams) -> Dict:
        df = self.df.copy()
        df["pivot_high"] = self._pivot_high(df["high"], params.left_bars, params.right_bars)
        df["pivot_low"] = self._pivot_low(df["low"], params.left_bars, params.right_bars)

        resistance = np.nan
        support = np.nan
        position: Optional[Dict] = None
        trades: List[Dict] = []
        cooldown_counter = params.cooldown_bars + 1
        equity = 1.0
        peak_equity = 1.0
        equity_curve = []

        breakout_checks = 0

        for idx, row in df.iterrows():
            price = row["close"]
            high = row["high"]
            low = row["low"]
            atr = row["atr14"]

            if not np.isnan(row["pivot_high"]):
                resistance = row["pivot_high"]
            if not np.isnan(row["pivot_low"]):
                support = row["pivot_low"]

            trend = price > row["ema200"]
            vol_osc = 100 * (row["vol_ema5"] - row["vol_ema10"]) / max(row["vol_ema10"], 1e-9)
            prev_close = df.at[idx - 1, "close"] if idx > 0 else df.at[idx, "close"]
            breakout_above = (
                not np.isnan(resistance)
                and trend
                and price > resistance
                and prev_close <= resistance
                and (vol_osc > params.volume_threshold or price > row["ema20"])
            )
            if breakout_above:
                breakout_checks += 1

            if position:
                exit_reason = None
                exit_price = None

                # Update trailing stop
                if not np.isnan(atr):
                    trail_candidate = price - atr * params.trail_atr_offset
                    if trail_candidate > position["trail_stop"]:
                        position["trail_stop"] = trail_candidate

                # Evaluate exits
                if low <= position["stop_price"]:
                    exit_price = position["stop_price"]
                    exit_reason = "stop"
                elif high >= position["tp_price"]:
                    exit_price = position["tp_price"]
                    exit_reason = "target"
                elif low <= position["trail_stop"]:
                    exit_price = position["trail_stop"]
                    exit_reason = "trail"

                if exit_price is not None:
                    gross_ret = (exit_price - position["entry_price"]) / position["entry_price"]
                    net_ret = gross_ret - 2 * self.fee_rate
                    equity *= (1 + net_ret)
                    peak_equity = max(peak_equity, equity)
                    trades.append(
                        {
                            "entry_time": position["entry_time"],
                            "exit_time": row["timestamp"],
                            "entry": position["entry_price"],
                            "exit": exit_price,
                            "return_pct": net_ret * 100,
                            "reason": exit_reason,
                        }
                    )
                    position = None
                    cooldown_counter = 0

            if position is None:
                cooldown_counter += 1

            if (
                position is None
                and breakout_above
                and cooldown_counter >= params.cooldown_bars
                and not np.isnan(resistance)
            ):
                entry_price = price
                position = {
                    "entry_price": entry_price,
                    "entry_time": row["timestamp"],
                    "stop_price": entry_price - atr * params.stop_multiplier if not np.isnan(atr) else entry_price * 0.99,
                    "tp_price": entry_price + atr * params.tp_atr_multiple if not np.isnan(atr) else entry_price * 1.02,
                    "trail_stop": entry_price - atr if not np.isnan(atr) else entry_price * 0.99,
                }
                cooldown_counter = 0

            equity_curve.append(equity)

        total_return = equity - 1.0
        max_drawdown = self._max_drawdown(pd.Series(equity_curve))

        return {
            "params": asdict(params),
            "trades": trades,
            "total_return_pct": total_return * 100,
            "num_trades": len(trades),
            "win_rate_pct": self._win_rate(trades),
            "max_drawdown_pct": max_drawdown * 100,
            "equity_curve": equity_curve,
            "breakout_signals": breakout_checks,
        }

    @staticmethod
    def _max_drawdown(equity: pd.Series) -> float:
        peak = equity.expanding(min_periods=1).max()
        dd = (equity - peak) / peak
        return dd.min()

    @staticmethod
    def _win_rate(trades: List[Dict]) -> float:
        if not trades:
            return 0.0
        wins = sum(1 for t in trades if t["return_pct"] > 0)
        return 100 * wins / len(trades)


