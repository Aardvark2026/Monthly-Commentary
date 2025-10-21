import pandas as pd
from pandas_datareader import data as pdr

from ..utils.io import cache_series


def fred_series(series: str, start="2000-01-01"):
    s = pdr.DataReader(series, "fred", start=start)
    s = s.dropna()
    s.name = series
    cache_series(s, f"fred_{series}")
    return s[series] if hasattr(s, "columns") else s


def yoy(series: pd.Series):
    m = series.resample("M").last()
    return ((m / m.shift(12) - 1.0) * 100.0).rename(series.name + "_YoY%")
