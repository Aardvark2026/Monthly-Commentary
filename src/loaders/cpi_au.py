"""AU CPI loader with best-effort parsing of ABS CSV."""

import io
import logging

import pandas as pd
import requests

from ..utils.io import cache_series

ABS_URL = "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/latest-release/640101.csv"
LOGGER = logging.getLogger(__name__)


def au_cpi_yoy():
    try:
        r = requests.get(ABS_URL, timeout=45)
        r.raise_for_status()
        df = pd.read_csv(io.BytesIO(r.content))
        date_col = [c for c in df.columns if "Date" in c or "Quarter" in c]
        val_col = [c for c in df.columns if "CPI" in c and "Index" in c]
        if not date_col or not val_col:
            LOGGER.warning("ABS CPI schema unexpected; date columns %s, value columns %s", date_col, val_col)
            return None
        s = pd.Series(df[val_col[0]].values, index=pd.to_datetime(df[date_col[0]]), name="AUCPI")
        yoy = (s / s.shift(4) - 1.0) * 100.0
        yoy = yoy.rename("AUCPI_YoY%").dropna()
        cache_series(yoy, "abs_aucpi_yoy")
        return yoy
    except Exception as exc:
        LOGGER.warning("Failed to load ABS CPI: %s", exc)
        return None
