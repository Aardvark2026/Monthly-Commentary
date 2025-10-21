from __future__ import annotations

import pandas as pd


def to_series(series: pd.Series | None) -> pd.Series:
    if series is None:
        return pd.Series(dtype=float)
    s = pd.Series(series).dropna()
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)
    s = s.sort_index()
    s.name = getattr(series, "name", s.name)
    return s


def monthly_last(series: pd.Series | None) -> pd.Series:
    s = to_series(series)
    if s.empty:
        return s
    return s.resample("M").last()


def last_value(series: pd.Series, timestamp: pd.Timestamp) -> float | None:
    if series is None or series.empty:
        return None
    filtered = series.loc[:timestamp].dropna()
    if filtered.empty:
        return None
    return float(filtered.iloc[-1])
