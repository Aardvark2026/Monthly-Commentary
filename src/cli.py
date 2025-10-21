from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .charts import audusd_vs_10y, commodities as commodities_chart, cpi_yoy as cpi_chart
from .charts import equities_vs_10y, policy_rates as policy_chart, tenor as tenor_chart
from .llm import generator as llm_generator, prompts, rules
from .loaders import commods
from .loaders.cpi_au import au_cpi_yoy
from .loaders.fred import fred_series, yoy
from .loaders.policy import fed_funds, rba_cash
from .loaders.rba import au_government_10y_series
from .loaders.yahoo import fetch_series
from .utils.dates import MonthWindow, parse_month
from .utils.io import (
    build_snapshot,
    direction_from_change,
    ensure_directory,
    format_percent,
    load_yaml,
    percent_change,
    write_excel,
    write_text,
)
from .utils.series import last_value, monthly_last, to_series

LOGGER = logging.getLogger("monthly_commentary")
ROOT = Path(__file__).resolve().parents[1]
# ROOT points at the repository root (../.. from this file). PROJECT_ROOT should be the repo root.
PROJECT_ROOT = ROOT
TEMPLATES = ROOT / "templates"
CONFIG_PATH = PROJECT_ROOT / "config" / "markets.yml"
DEFAULT_LOOKBACK_MONTHS = 24


class SectionMetrics(dict):
    def __init__(self, start: float | None, end: float | None, mom_pct: float | None):
        direction = direction_from_change(mom_pct)
        super().__init__(
            start=format_percent(start),
            end=format_percent(end),
            mom_pct=format_percent(mom_pct),
            direction=direction,
        )


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def _get_markets(selection: str | None) -> Iterable[str]:
    if not selection:
        return []
    return [item.strip() for item in selection.split(",") if item.strip()]


def load_market_config(selected: Iterable[str]) -> list[dict]:
    config = load_yaml(CONFIG_PATH)
    markets = config.get("markets", [])
    selected_set = set(selected) if selected else {m["code"] for m in markets}
    return [m for m in markets if m.get("code") in selected_set]


def _monthly_stats(series: pd.Series, window: MonthWindow) -> tuple[float | None, float | None, float | None]:
    if series is None or series.empty:
        return None, None, None
    monthly = monthly_last(series)
    end_val = last_value(monthly, window.end)
    prev_val = last_value(monthly, window.prev_end)
    change = percent_change(end_val, prev_val)
    return prev_val, end_val, change


def _series_to_snapshot_map(data: dict[str, pd.Series]) -> dict[str, pd.Series]:
    return {name: to_series(series) for name, series in data.items() if series is not None}


def _render_template(context: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=select_autoescape(enabled_extensions=(".j2",)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("commentary.md.j2")
    return template.render(**context)


def _try_llm(prompt: str, fallback: str) -> str:
    generated = llm_generator.run_prompt(prompt)
    if generated:
        return generated.strip()
    return fallback


def _format_return(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}"


def run(month: str, markets: str, outputs: str, lookback: int = DEFAULT_LOOKBACK_MONTHS, verbose: bool = False) -> None:
    _setup_logging(verbose)
    window = parse_month(month)
    LOGGER.info("Running monthly commentary for %s", window.label)
    output_set = {opt.strip() for opt in outputs.split(",") if opt.strip()}
    selected_markets = list(_get_markets(markets))
    market_configs = load_market_config(selected_markets)
    if not market_configs:
        raise ValueError("No markets selected")

    lookback_months = lookback

    # Load rates and equities
    market_data: dict[str, dict[str, pd.Series]] = {}
    from src.loaders.yahoo import LoaderEmptyError
    for market in market_configs:
        code = market["code"]
        ten_year_ticker = market.get("ten_year_ticker")
        equity_ticker = market.get("equity_ticker")
        ten_year_series = None
        try:
            ten_year_series = fetch_series(ten_year_ticker, window, lookback_months)
            if code == "us":
                ten_year_series = ten_year_series / 10.0
                ten_year_series.name = "US10Y"
            elif code == "au" and ten_year_series.dropna().empty:
                raise LoaderEmptyError("Yahoo AU 10y empty, try RBA fallback")
        except LoaderEmptyError:
            if code == "au":
                LOGGER.info("Yahoo AU 10y unavailable; attempting RBA fallback")
                ten_year_series = to_series(au_government_10y_series())
                if ten_year_series is None or ten_year_series.dropna().empty:
                    LOGGER.warning("RBA AU 10y fallback failed; marking AU 10y as None")
                    ten_year_series = pd.Series(dtype=float)
            elif code == "us":
                LOGGER.info("Yahoo US 10y unavailable; attempting FRED fallback")
                try:
                    ten_year_series = to_series(fred_series("GS10"))
                    ten_year_series = ten_year_series / 10.0
                    ten_year_series.name = "US10Y"
                except Exception as exc:
                    LOGGER.warning(f"FRED US 10y fallback failed: {exc}; marking US 10y as None")
                    ten_year_series = pd.Series(dtype=float)
        equity_series = None
        try:
            equity_series = fetch_series(equity_ticker, window, lookback_months)
        except LoaderEmptyError:
            LOGGER.warning(f"Equity series {equity_ticker} failed; marking as None")
            equity_series = pd.Series(dtype=float)
        market_data[code] = {
            "ten_year": to_series(ten_year_series),
            "equity": to_series(equity_series),
        }

    # FX and commodities
    config = load_yaml(CONFIG_PATH)
    fx_cfg = config.get("fx", {})
    commodities_cfg = config.get("commodities", {})

    # FX
    try:
        audusd_series = to_series(fetch_series(fx_cfg.get("audusd"), window, lookback_months))
    except LoaderEmptyError:
        LOGGER.warning("AUDUSD series failed; marking as None")
        audusd_series = pd.Series(dtype=float)
    try:
        dxy_series = to_series(fetch_series(fx_cfg.get("dxy_proxy"), window, lookback_months))
    except LoaderEmptyError:
        LOGGER.warning("UUP/DXY series failed; marking as None")
        dxy_series = pd.Series(dtype=float)

    # Commodities
    try:
        gold_series = to_series(commods.load_gold(window, lookback_months))
    except LoaderEmptyError:
        LOGGER.warning("Gold series failed; marking as None")
        gold_series = pd.Series(dtype=float)
    try:
        wti_series = to_series(commods.load_wti(window, lookback_months))
    except LoaderEmptyError:
        LOGGER.warning("WTI series failed; marking as None")
        wti_series = pd.Series(dtype=float)
    try:
        brent_series = to_series(commods.load_brent(window, lookback_months))
    except LoaderEmptyError:
        LOGGER.warning("Brent series failed; marking as None")
        brent_series = pd.Series(dtype=float)
    try:
        iron_series_raw = commods.load_iron_ore(
            window,
            lookback_months,
            commodities_cfg.get("iron_ore_candidates", []),
            commodities_cfg.get("iron_ore_tradingeconomics_series"),
        )
        iron_series = to_series(iron_series_raw) if iron_series_raw is not None else None
        if iron_series is not None and iron_series.empty:
            iron_series = None
    except LoaderEmptyError:
        LOGGER.warning("Iron ore series failed; marking as None")
        iron_series = None

    # CPI
    us_cpi = to_series(fred_series("CPIAUCSL"))
    us_cpi_yoy = yoy(us_cpi)
    au_cpi_yoy_series = au_cpi_yoy()
    au_cpi_series = to_series(au_cpi_yoy_series) if au_cpi_yoy_series is not None else pd.Series(dtype=float)

    # Policy
    fed_series = to_series(fed_funds())
    rba_series = to_series(rba_cash())

    # Compute metrics
    us_rates = market_data.get("us", {})
    au_rates = market_data.get("au", {})
    us_10y_prev, us_10y_end, us_10y_mom = _monthly_stats(us_rates.get("ten_year"), window)
    au_10y_prev, au_10y_end, au_10y_mom = _monthly_stats(au_rates.get("ten_year"), window)
    spx_prev, spx_end, spx_mom = _monthly_stats(us_rates.get("equity"), window)
    axjo_prev, axjo_end, axjo_mom = _monthly_stats(au_rates.get("equity"), window)
    audusd_prev, audusd_end, audusd_mom = _monthly_stats(audusd_series, window)
    dxy_prev, dxy_end, dxy_mom = _monthly_stats(dxy_series, window)
    gold_prev, gold_end, gold_mom = _monthly_stats(gold_series, window)
    wti_prev, wti_end, wti_mom = _monthly_stats(wti_series, window)
    brent_prev, brent_end, brent_mom = _monthly_stats(brent_series, window)
    iron_prev, iron_end, iron_mom = _monthly_stats(iron_series, window) if iron_series is not None else (None, None, None)

    us_cpi_val = last_value(us_cpi_yoy, window.end)
    au_cpi_val = last_value(au_cpi_series, window.end)
    fed_last = last_value(fed_series, window.end)
    rba_last = last_value(rba_series, window.end)

    # Build paragraphs
    bond_facts = f"US 10y {format_percent(us_10y_prev)} → {format_percent(us_10y_end)} ({format_percent(us_10y_mom)} MoM); AU 10y {format_percent(au_10y_prev)} → {format_percent(au_10y_end)} ({format_percent(au_10y_mom)} MoM)."
    equity_facts = f"S&P 500 {format_percent(spx_mom)} MoM; ASX 200 {format_percent(axjo_mom)} MoM."
    fx_facts = f"AUDUSD {format_percent(audusd_mom)} MoM; UUP {format_percent(dxy_mom)} MoM."
    cpi_facts = f"US CPI YoY {format_percent(us_cpi_val)}; AU CPI YoY {format_percent(au_cpi_val)}."
    policy_facts = f"Fed funds {format_percent(fed_last)}; RBA cash {format_percent(rba_last)}."
    cmdty_facts = f"Gold {format_percent(gold_mom)}; WTI {format_percent(wti_mom)}; Brent {format_percent(brent_mom)}" + (f"; Iron ore {format_percent(iron_mom)}." if iron_mom is not None else ". Iron ore: n/a.")

    bond_para = _try_llm(prompts.BOND_PROMPT.format(facts=bond_facts), rules.bond_summary(us_10y_end, us_10y_mom, au_10y_end, au_10y_mom))
    equity_para = _try_llm(prompts.EQUITY_PROMPT.format(facts=equity_facts), rules.equity_summary(spx_mom, axjo_mom))
    fx_para = _try_llm(prompts.FX_PROMPT.format(facts=fx_facts), rules.fx_summary(audusd_mom, dxy_mom))
    cpi_para = _try_llm(prompts.CPI_PROMPT.format(facts=cpi_facts), rules.cpi_summary(us_cpi_val, au_cpi_val))
    policy_para = _try_llm(prompts.POLICY_PROMPT.format(facts=policy_facts), rules.policy_summary(fed_last, rba_last))
    cmdty_para = _try_llm(prompts.CMDTY_PROMPT.format(facts=cmdty_facts), rules.commodity_summary(gold_mom, wti_mom, brent_mom, iron_mom))

    context = {
        "month": window.label,
        "us_10y": SectionMetrics(us_10y_prev, us_10y_end, us_10y_mom),
        "au_10y": SectionMetrics(au_10y_prev, au_10y_end, au_10y_mom),
        "us_cpi_yoy": format_percent(us_cpi_val) if us_cpi_val is not None else "n/a",
        "au_cpi_yoy": format_percent(au_cpi_val) if au_cpi_val is not None else "n/a",
        "fed_last": format_percent(fed_last) if fed_last is not None else "n/a",
        "rba_last": format_percent(rba_last) if rba_last is not None else "n/a",
        "spx_ret": format_percent(spx_mom) if spx_mom is not None else "n/a",
        "axjo_ret": format_percent(axjo_mom) if axjo_mom is not None else "n/a",
        "audusd_ret": format_percent(audusd_mom) if audusd_mom is not None else "n/a",
        "dxy_ret": format_percent(dxy_mom) if dxy_mom is not None else "n/a",
        "gold_ret": format_percent(gold_mom) if gold_mom is not None else "n/a",
        "wti_ret": format_percent(wti_mom) if wti_mom is not None else "n/a",
        "brent_ret": format_percent(brent_mom) if brent_mom is not None else "n/a",
        "iron_ret": format_percent(iron_mom) if iron_mom is not None else "n/a",
        "para_bond": bond_para,
        "para_equities": equity_para,
        "para_fx": fx_para,
        "para_cpi": cpi_para,
        "para_policy": policy_para,
        "para_cmdty": cmdty_para,
    }

    report_dir = PROJECT_ROOT / "reports" / window.label
    charts_dir = report_dir / "charts"
    snapshots_dir = report_dir / "snapshots"
    ensure_directory(report_dir)
    ensure_directory(charts_dir)
    ensure_directory(snapshots_dir)

    # Render markdown
    md_content = _render_template(context)
    if "md" in output_set:
        write_text(report_dir / "monthly_commentary.md", md_content)

    # Excel workbook

    def _df_diag(name, df):
        print(f"[DIAG] {name}: shape={df.shape}")
        print(df.head())
        print(df.tail())
        if df.empty or df.isna().all().all():
            print(f"[WARNING] {name} is empty or all-NaN!")

    sheets: dict[str, pd.DataFrame] = {}
    rates_df = pd.concat([
        monthly_last(market_data["us"]["ten_year"]).rename("US 10y"),
        monthly_last(market_data["au"].get("ten_year")).rename("AU 10y") if "au" in market_data else None,
    ], axis=1)
    _df_diag("Rates", rates_df)
    sheets["Rates"] = rates_df

    cpi_df = pd.concat([
        us_cpi_yoy.rename("US CPI YoY %"),
        au_cpi_series.rename("AU CPI YoY %") if not au_cpi_series.empty else None,
    ], axis=1)
    _df_diag("CPI", cpi_df)
    sheets["CPI"] = cpi_df

    policy_df = pd.concat([
        fed_series.rename("Fed Funds %"),
        rba_series.rename("RBA Cash %"),
    ], axis=1)
    _df_diag("Policy", policy_df)
    sheets["Policy"] = policy_df

    equities_df = pd.concat([
        monthly_last(market_data["us"]["equity"]).rename("S&P 500"),
        monthly_last(market_data["au"].get("equity")).rename("ASX 200") if "au" in market_data else None,
    ], axis=1)
    _df_diag("Equities", equities_df)
    sheets["Equities"] = equities_df

    fx_df = pd.concat([
        monthly_last(audusd_series).rename("AUDUSD"),
        monthly_last(dxy_series).rename("UUP"),
    ], axis=1)
    _df_diag("FX", fx_df)
    sheets["FX"] = fx_df

    commodities_df = pd.concat([
        monthly_last(gold_series).rename("Gold"),
        monthly_last(wti_series).rename("WTI"),
        monthly_last(brent_series).rename("Brent"),
        monthly_last(iron_series).rename("Iron Ore") if iron_series is not None else None,
    ], axis=1)
    _df_diag("Commodities", commodities_df)
    sheets["Commodities"] = commodities_df

    workbook_commentary = "\n".join([
        context["para_bond"],
        context["para_cpi"],
        context["para_policy"],
        context["para_equities"],
        context["para_fx"],
        context["para_cmdty"],
    ])
    if "xlsx" in output_set:
        write_excel(report_dir / "dashboard.xlsx", sheets, workbook_commentary)

    # Charts
    tenor_chart.plot(market_data["us"]["ten_year"], market_data.get("au", {}).get("ten_year"), str(charts_dir / "tenor_10y_trend.png"))
    equities_vs_10y.plot(
        monthly_last(market_data["us"]["equity"]).pct_change() * 100.0,
        monthly_last(market_data["us"]["ten_year"]).pct_change() * 100.0,
        str(charts_dir / "equities_vs_10y.png"),
    )
    audusd_vs_10y.plot(
        monthly_last(audusd_series).pct_change() * 100.0,
        monthly_last(market_data["us"]["ten_year"]).pct_change() * 100.0,
        str(charts_dir / "audusd_vs_10y.png"),
    )
    cpi_chart.plot(us_cpi_yoy, au_cpi_series, str(charts_dir / "cpi_yoy.png"))
    policy_chart.plot(fed_series, rba_series, str(charts_dir / "policy_rates.png"))
    commodities_chart.plot(gold_series, wti_series, brent_series, iron_series, str(charts_dir / "commodities.png"))

    # Snapshots
    snapshot_series = {
        "us_10y": market_data["us"]["ten_year"],
        "au_10y": market_data.get("au", {}).get("ten_year"),
        "spx": market_data["us"]["equity"],
        "axjo": market_data.get("au", {}).get("equity"),
        "audusd": audusd_series,
        "uup": dxy_series,
        "gold": gold_series,
        "wti": wti_series,
        "brent": brent_series,
        "ironore": iron_series,
        "us_cpi_yoy": us_cpi_yoy,
        "au_cpi_yoy": au_cpi_series,
        "fed_funds": fed_series,
        "rba_cash": rba_series,
    }
    build_snapshot(_series_to_snapshot_map(snapshot_series), snapshots_dir)

    LOGGER.info("Report generated at %s", report_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Monthly commentary generator")
    parser.add_argument("--month", default="auto", help="Target month in YYYY-MM or 'auto'")
    parser.add_argument("--markets", default="us,au", help="Comma separated market codes")
    parser.add_argument("--outputs", default="md,xlsx", help="Comma separated outputs (md,xlsx)")
    parser.add_argument("--lookback", type=int, default=DEFAULT_LOOKBACK_MONTHS, help="Months of history to load")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    run(args.month, args.markets, args.outputs, args.lookback, args.verbose)


if __name__ == "__main__":
    main()
