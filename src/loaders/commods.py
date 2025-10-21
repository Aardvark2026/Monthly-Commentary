from __future__ import annotations

import os
import logging

import pandas as pd
import requests

from .yahoo import fetch_series
from ..utils.io import cache_series

LOGGER = logging.getLogger(__name__)


def load_gold(month, lookback):
    return fetch_series("GC=F", month, lookback)


def load_wti(month, lookback):
    return fetch_series("CL=F", month, lookback)


def load_brent(month, lookback):
    return fetch_series("BZ=F", month, lookback)


def load_iron_ore(month, lookback, candidates: list[str], te_series: str | None):
    for ticker in candidates:
        try:
            s = fetch_series(ticker, month, lookback)
            if not s.dropna().empty:
                s.name = "IRONORE"
                return s
        except Exception:
            continue
    key = os.getenv("TE_API_KEY")
    if key and te_series:
        try:
            url = f"https://api.tradingeconomics.com/commodities/{te_series}?c=guest:{key}&format=json"
            resp = requests.get(url, timeout=45)
            resp.raise_for_status()
            js = resp.json()
            df = pd.DataFrame(js)
            if "Date" in df.columns and "Value" in df.columns:
                series = pd.Series(df["Value"].values, index=pd.to_datetime(df["Date"]), name="IRONORE")
                series = series.sort_index()
                cache_series(series, "te_ironore")
                return series
        except Exception as exc:
            LOGGER.warning("TradingEconomics iron ore fetch failed: %s", exc)
    return None
