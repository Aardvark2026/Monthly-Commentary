from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import pandas as pd


@dataclass(frozen=True)
class MonthWindow:
    label: str
    start: pd.Timestamp
    end: pd.Timestamp
    prev_end: pd.Timestamp


def parse_month(value: str | None) -> MonthWindow:
    """Parse a YYYY-MM string and return boundaries (inclusive).

    If value is ``auto`` or ``None``, the window defaults to the previous
    calendar month relative to today (UTC).
    """

    if value in (None, "auto"):
        today = datetime.utcnow().date()
        first_this_month = today.replace(day=1)
        prev_month_end = first_this_month - relativedelta(days=1)
        target = prev_month_end.replace(day=1)
    else:
        try:
            target = datetime.strptime(value, "%Y-%m").date()
        except ValueError as exc:
            raise ValueError("month must be in YYYY-MM format or 'auto'") from exc

    start = pd.Timestamp(target)
    end = (start + relativedelta(months=1)) - relativedelta(days=1)
    prev_end = start - relativedelta(days=1)
    label = start.strftime("%Y-%m")
    return MonthWindow(label=label, start=start, end=end, prev_end=prev_end)


def month_lookback_start(window: MonthWindow, months: int = 24) -> pd.Timestamp:
    """Return the first timestamp required to cover ``months`` before ``window``."""

    start = window.start - relativedelta(months=months)
    return pd.Timestamp(start)
