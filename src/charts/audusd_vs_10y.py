import matplotlib.pyplot as plt
import pandas as pd


def plot(audusd_mom: pd.Series, us10y_mom: pd.Series, path: str, width: int = 900, height: int = 500):
    df = pd.concat([
        audusd_mom.rename("AUDUSD MoM %"),
        us10y_mom.rename("US 10y MoM %"),
    ], axis=1)
    df = df.dropna(how="all")
    plt.figure(figsize=(width / 100, height / 100))
    if not df.empty:
        df.plot(ax=plt.gca())
    plt.title("AUDUSD vs US 10y (MoM %)")
    plt.ylabel("%")
    plt.xlabel("")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
