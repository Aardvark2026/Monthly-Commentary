from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "data" / "cache"


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def cache_series(series: pd.Series, name: str) -> None:
    if series is None:
        return
    ensure_directory(CACHE_DIR)
    csv_path = CACHE_DIR / f"{name}.csv"
    json_path = CACHE_DIR / f"{name}.json"
    try:
        series.to_csv(csv_path, header=True)
        meta = {
            "name": name,
            "rows": int(series.dropna().shape[0]),
            "cached_at": datetime.utcnow().isoformat() + "Z",
        }
        json_path.write_text(json.dumps(meta, indent=2))
    except Exception as exc:
        logging.getLogger(__name__).warning("Failed to cache %s: %s", name, exc)


def cache_frame(frame: pd.DataFrame, name: str) -> None:
    ensure_directory(CACHE_DIR)
    csv_path = CACHE_DIR / f"{name}.csv"
    json_path = CACHE_DIR / f"{name}.json"
    try:
        frame.to_csv(csv_path, index=True)
        meta = {
            "name": name,
            "rows": int(frame.dropna(how="all").shape[0]),
            "cached_at": datetime.utcnow().isoformat() + "Z",
        }
        json_path.write_text(json.dumps(meta, indent=2))
    except Exception as exc:
        logging.getLogger(__name__).warning("Failed to cache frame %s: %s", name, exc)


def write_snapshot(series: pd.Series, path: Path) -> None:
    ensure_directory(path.parent)
    data = [
        {
            "date": (idx.isoformat() if isinstance(idx, pd.Timestamp) else str(idx)),
            "value": (None if pd.isna(val) else float(val)),
        }
        for idx, val in series.items()
    ]
    path.write_text(json.dumps(data, indent=2))


def write_text(path: Path, text: str) -> None:
    ensure_directory(path.parent)
    path.write_text(text)


def write_excel(path: Path, sheets: dict[str, pd.DataFrame], commentary: str) -> None:
    def safe_df(df):
        # Replace NaNs with 'n/a', keep number formatting for numeric columns
        return df.copy().where(df.notna(), other="n/a")

    ensure_directory(path.parent)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet, df in sheets.items():
            df_out = safe_df(df)
            df_out.to_excel(writer, sheet_name=sheet, index=True)
        comment_df = pd.DataFrame({"Commentary": commentary.splitlines()})
        comment_df.to_excel(writer, sheet_name="Commentary", index=False)


def load_yaml(path: Path) -> dict:
    import yaml

    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def format_percent(value: float | None, decimals: int = 2) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{value:.{decimals}f}"


def direction_from_change(change: float | None) -> str:
    if change is None or pd.isna(change):
        return "was little changed"
    if change > 0:
        return "rose"
    if change < 0:
        return "fell"
    return "was little changed"


def safe_last(series: pd.Series, upto: pd.Timestamp) -> float | None:
    if series is None:
        return None
    trimmed = series.dropna()
    trimmed = trimmed.loc[:upto]
    if trimmed.empty:
        return None
    return float(trimmed.iloc[-1])


def safe_previous(series: pd.Series, upto: pd.Timestamp) -> float | None:
    if series is None:
        return None
    trimmed = series.dropna()
    trimmed = trimmed.loc[:upto]
    if trimmed.empty:
        return None
    if trimmed.size == 1:
        return None
    return float(trimmed.iloc[-2])


def percent_change(new: float | None, old: float | None) -> float | None:
    if new is None or old is None or old == 0:
        return None
    return (new / old - 1.0) * 100.0


def build_snapshot(series_map: dict[str, pd.Series], base_path: Path) -> None:
    for name, series in series_map.items():
        if series is None:
            continue
        write_snapshot(series.dropna(), base_path / f"{name}.json")
