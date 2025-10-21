import matplotlib.pyplot as plt
import pandas as pd


def plot(us_10y: pd.Series, au_10y: pd.Series, path: str, width: int = 900, height: int = 500):
    plt.figure(figsize=(width / 100, height / 100))
    df = pd.concat([
        us_10y.rename("US 10y"),
        au_10y.rename("AU 10y") if au_10y is not None else None,
    ], axis=1)
    df = df.dropna(how="all")
    if df.empty:
        plt.title("10-Year Government Bond Yields")
    else:
        df.resample("M").last().plot(ax=plt.gca())
        plt.title("10-Year Government Bond Yields")
        plt.ylabel("%")
        plt.xlabel("")
        plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
