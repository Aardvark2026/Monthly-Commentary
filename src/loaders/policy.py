from .fred import fred_series
from .rba import au_cash_rate_series


def fed_funds():
    return fred_series("FEDFUNDS")


def rba_cash():
    return au_cash_rate_series()
