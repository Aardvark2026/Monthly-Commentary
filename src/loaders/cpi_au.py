"""AU CPI loader with best-effort parsing of ABS CSV."""

import io
import logging

import pandas as pd
import requests

from ..utils.io import cache_series
from ..transforms.fill import ensure_datetime_index

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
        yoy = yoy.rename("AUCPI_YoY%").dropna().round(2).astype(float)
        cache_series(yoy, "abs_aucpi_yoy")
        return yoy
    except Exception as exc:
        LOGGER.warning("Failed to load ABS CPI: %s", exc)
        # RBA fallback (headline quarterly)
        try:
            url = "https://www.rba.gov.au/statistics/tables/csv/f01.1-data.csv"
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            df = pd.read_csv(io.BytesIO(r.content))
            date_col = df.columns[0]
            val_col = [c for c in df.columns if "headline" in c.lower() and "cpi" in c.lower()]
            if not val_col:
                LOGGER.warning("RBA fallback CPI: headline column not found")
                return None
            s = pd.Series(df[val_col[0]].values, index=pd.to_datetime(df[date_col]), name="AUCPI_RBA")
            s = ensure_datetime_index(s)
            yoy = (s / s.shift(4) - 1.0) * 100.0
            yoy = yoy.rename("AUCPI_YoY%_RBA").dropna().round(2).astype(float)
            cache_series(yoy, "rba_aucpi_yoy")
            return yoy
        except Exception as exc2:
            LOGGER.warning("RBA fallback CPI failed: %s", exc2)
            return None
