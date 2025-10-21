import matplotlib.pyplot as plt
import pandas as pd


def plot(equity_mom: pd.Series, yield_mom: pd.Series, path: str, width: int = 900, height: int = 500):
    df = pd.concat([
        equity_mom.rename("S&P 500 MoM %"),
        yield_mom.rename("US 10y MoM %"),
    ], axis=1)
    df = df.dropna(how="all")
    plt.figure(figsize=(width / 100, height / 100))
    if not df.empty:
        df.plot(ax=plt.gca())
    plt.title("S&P 500 vs US 10y (MoM %)")
    plt.ylabel("%")
    plt.xlabel("")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
