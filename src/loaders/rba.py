import io
import logging

import pandas as pd
import requests

from ..utils.io import cache_series

RBA_CASH_URL = "https://www.rba.gov.au/statistics/cash-rate.csv"
RBA_10Y_URL = "https://www.rba.gov.au/statistics/tables/csv/f16.1-data.csv"
LOGGER = logging.getLogger(__name__)


def au_cash_rate_series():
    try:
        r = requests.get(RBA_CASH_URL, timeout=30)
        r.raise_for_status()
        df = pd.read_csv(io.BytesIO(r.content))
        date_col = df.columns[0]
        rate_col = [c for c in df.columns if "Cash" in c and "Rate" in c]
        if not rate_col:
            LOGGER.warning("Could not find cash rate column in RBA dataset: %s", df.columns)
            return None
        s = pd.Series(df[rate_col[0]].values, index=pd.to_datetime(df[date_col]), name="RBACASH")
        s = s.dropna()
        cache_series(s, "rba_cash_rate")
        return s
    except Exception as exc:
        LOGGER.warning("Failed to load RBA cash rate: %s", exc)
        return None


def au_government_10y_series():
    """Attempt to retrieve Australian 10y yields from the RBA.

    The CSV layout is subject to change; this function relies on heuristic
    column matching and returns ``None`` if parsing fails.
    """

    try:
        r = requests.get(RBA_10Y_URL, timeout=45)
        r.raise_for_status()
        raw_df = pd.read_csv(io.BytesIO(r.content))
    except Exception as exc:
        LOGGER.warning("Failed to download RBA 10y yields: %s", exc)
        return None

    try:
        df = raw_df.copy()
        df = df.dropna(how="all")
        first_col = df.columns[0]
        df = df[df[first_col].notna()]
        df[first_col] = pd.to_datetime(df[first_col], errors="coerce")
        df = df.dropna(subset=[first_col])
        value_cols = [
            c for c in df.columns if "10" in str(c) and "year" in str(c).lower()
        ]
        if not value_cols:
            LOGGER.warning("No 10-year column detected in RBA data: %s", df.columns)
            return None
        series = pd.Series(df[value_cols[0]].values, index=df[first_col], name="AU10Y")
        series = series.astype(float).dropna()
        cache_series(series, "rba_au10y")
        return series
    except Exception as exc:
        LOGGER.warning("Failed to parse RBA 10y yields: %s", exc)
        return None
