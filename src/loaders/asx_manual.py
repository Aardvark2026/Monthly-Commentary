import os
import pandas as pd
from ..utils.io import cache_series

def asx200_manual_series():
    manual_path = os.path.join(os.path.dirname(__file__), '../../data/asx200_manual.csv')
    if os.path.exists(manual_path):
        try:
            df = pd.read_csv(manual_path)
            date_col = df.columns[0]
            val_col = df.columns[1]
            s = pd.Series(df[val_col].values, index=pd.to_datetime(df[date_col]), name="ASX200_MANUAL")
            s = s.dropna()
            cache_series(s, "asx200_manual")
            return s
        except Exception as exc:
            print(f"Manual ASX200 CSV failed: {exc}")
    return None