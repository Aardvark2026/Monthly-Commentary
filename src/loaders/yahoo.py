from __future__ import annotations

import logging
from datetime import timedelta
from typing import Optional

import pandas as pd
import yfinance as yf

from ..utils.dates import MonthWindow, month_lookback_start
from ..utils.io import cache_series

LOGGER = logging.getLogger(__name__)


def _resolve_window(month: MonthWindow | str) -> MonthWindow:
    from ..utils.dates import parse_month

    if isinstance(month, MonthWindow):
        return month
    return parse_month(month)


def fetch_series(ticker: str, month: MonthWindow | str, lookback_months: int = 24) -> pd.Series:
    window = _resolve_window(month)
    start = month_lookback_start(window, lookback_months)
    end = window.end + timedelta(days=7)
    try:
        df = yf.download(ticker, start=start.to_pydatetime(), end=end.to_pydatetime(), progress=False, auto_adjust=False)
        if df.empty:
            raise ValueError("empty frame")
        series = df["Adj Close" if "Adj Close" in df.columns else "Close"]
        series.index = pd.to_datetime(series.index)
        series.name = ticker
        cache_series(series, f"yahoo_{ticker.replace('^', '').replace('=', '_')}")
        return series
    except Exception as exc:
        LOGGER.warning("Failed to fetch %s from Yahoo Finance: %s", ticker, exc)
        return pd.Series(dtype=float, name=ticker)


def fetch_last_price(ticker: str) -> Optional[float]:
    try:
        series = yf.Ticker(ticker).history(period="1d")
        if series.empty:
            return None
        value = series["Adj Close" if "Adj Close" in series.columns else "Close"].iloc[-1]
        return float(value)
    except Exception as exc:
        LOGGER.warning("Failed to fetch last price for %s: %s", ticker, exc)
        return None
