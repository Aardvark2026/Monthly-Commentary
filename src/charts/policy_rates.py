import matplotlib.pyplot as plt
import pandas as pd


def plot(fed: pd.Series, rba: pd.Series, path: str, width=900, height=500):
    df = pd.concat([fed.rename("Fed Funds %"), rba.rename("RBA Cash %")], axis=1)
    df = df.dropna(how="all")
    plt.figure(figsize=(width / 100, height / 100))
    if not df.empty:
        df.plot(ax=plt.gca())
    plt.title("Policy Rates")
    plt.ylabel("%")
    plt.xlabel("")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
