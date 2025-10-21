import matplotlib.pyplot as plt
import pandas as pd


def _rebase(df, base_periods=12):
    if df.empty:
        return df
    m = df.resample("M").last()
    base = m.shift(base_periods).iloc[-1]
    rebased = m / base * 100.0
    return rebased.dropna(how="all")


def plot(gold, wti, brent, iron, path: str, width=900, height=500):
    series_list = [
        gold.rename("Gold") if gold is not None else None,
        wti.rename("WTI") if wti is not None else None,
        brent.rename("Brent") if brent is not None else None,
        iron.rename("Iron Ore") if iron is not None else None,
    ]
    df = pd.concat([s for s in series_list if s is not None], axis=1)
    df = df.dropna(how="all")
    plt.figure(figsize=(width / 100, height / 100))
    if not df.empty:
        rb = _rebase(df, 12)
        rb.plot(ax=plt.gca())
    plt.title("Commodities (Indexed = 100, T-12)")
    plt.ylabel("Index")
    plt.xlabel("")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
