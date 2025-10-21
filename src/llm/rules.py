from __future__ import annotations

from typing import Optional


def _format_change(value: float | None, precision: int = 2) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{precision}f}%"


def bond_summary(us_end: float | None, us_mom: float | None, au_end: float | None, au_mom: float | None) -> str:
    return (
        "US 10-year yields {us_dir} to {us_end}, a {us_mom} move on the month, while Australian "
        "10-year yields {au_dir} to {au_end} ({au_mom})."
    ).format(
        us_dir=_direction_phrase(us_mom),
        us_end=_level_phrase(us_end),
        us_mom=_format_change(us_mom),
        au_dir=_direction_phrase(au_mom),
        au_end=_level_phrase(au_end),
        au_mom=_format_change(au_mom),
    )


def cpi_summary(us_yoy: float | None, au_yoy: float | None) -> str:
    return (
        "US CPI is running at {us_yoy}, while Australian CPI is at {au_yoy}."
    ).format(us_yoy=_format_change(us_yoy), au_yoy=_format_change(au_yoy))


def policy_summary(fed: float | None, rba: float | None) -> str:
    return (
        "The Fed funds rate sits at {fed}, compared with the RBA cash rate at {rba}."
    ).format(fed=_format_change(fed), rba=_format_change(rba))


def equity_summary(spx_mom: float | None, axjo_mom: float | None) -> str:
    return (
        "The S&P 500 returned {spx} over the month, while the ASX 200 delivered {axjo}."
    ).format(spx=_format_change(spx_mom), axjo=_format_change(axjo_mom))


def fx_summary(audusd_mom: float | None, dxy_mom: float | None) -> str:
    return (
        "AUD/USD moved {aud} in monthly terms and the UUP dollar index proxy returned {dxy}."
    ).format(aud=_format_change(audusd_mom), dxy=_format_change(dxy_mom))


def commodity_summary(gold_mom: float | None, wti_mom: float | None, brent_mom: float | None, iron_mom: Optional[float]) -> str:
    iron_text = "Iron ore was unavailable." if iron_mom is None else f"Iron ore moved {_format_change(iron_mom)}."
    return (
        "Gold returned {gold}, WTI crude {wti}, and Brent {brent}. {iron}"
    ).format(
        gold=_format_change(gold_mom),
        wti=_format_change(wti_mom),
        brent=_format_change(brent_mom),
        iron=iron_text,
    )


def _direction_phrase(change: float | None) -> str:
    if change is None:
        return "was little changed"
    if change > 0:
        return "rose"
    if change < 0:
        return "fell"
    return "was little changed"


def _level_phrase(level: float | None) -> str:
    if level is None:
        return "n/a"
    return f"{level:.2f}%"
