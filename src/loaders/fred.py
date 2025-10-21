import pandas as pd
from pandas_datareader import data as pdr
import requests
import io

from ..utils.io import cache_series


def fred_series(series: str, start="2000-01-01"):
    try:
        s = pdr.DataReader(series, "fred", start=start)
        s = s.dropna()
        s.name = series
        cache_series(s, f"fred_{series}")
        return s[series] if hasattr(s, "columns") else s
    except Exception as exc:
        # CSV fallback for CPIAUCSL
        if series == "CPIAUCSL":
            url = "https://fred.stlouisfed.org/data/" + series + ".csv"
            try:
                r = requests.get(url, timeout=30)
                r.raise_for_status()
                df = pd.read_csv(io.StringIO(r.text))
                df["DATE"] = pd.to_datetime(df["DATE"])
                s = pd.Series(df[series].values, index=df["DATE"], name=series)
                s = s.dropna()
                cache_series(s, f"fred_{series}_csv")
                return s
            except Exception as exc2:
                print(f"[FRED Fallback] Failed to fetch {series} from CSV: {exc2}")
                return pd.Series(dtype=float, name=series)
        print(f"[FRED] Failed to fetch {series}: {exc}")
        return pd.Series(dtype=float, name=series)


def yoy(series: pd.Series):
    m = series.resample("M").last()
    return ((m / m.shift(12) - 1.0) * 100.0).rename(series.name + "_YoY%")
