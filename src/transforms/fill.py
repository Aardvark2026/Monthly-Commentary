import pandas as pd

def ensure_datetime_index(s):
    """Ensure the Series/DataFrame has a tz-naive DatetimeIndex."""
    idx = pd.to_datetime(s.index)
    idx = idx.tz_localize(None) if idx.tzinfo else idx
    s.index = idx
    return s

def month_last(s):
    """Robust monthly last using daily pad."""
    s = ensure_datetime_index(s)
    return s.resample("D").last().ffill().resample("M").last()

def mom_pct(s):
    """Monthly percentage change on month_last."""
    s = month_last(s)
    return s.pct_change() * 100.0
