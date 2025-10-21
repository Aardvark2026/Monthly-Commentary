import matplotlib.pyplot as plt
import pandas as pd


def plot(us_cpi_yoy: pd.Series, au_cpi_yoy: pd.Series, path: str, width=900, height=500):
    df = pd.concat([us_cpi_yoy.rename("US CPI YoY %"), au_cpi_yoy.rename("AU CPI YoY %")], axis=1)
    df = df.dropna(how="all")
    plt.figure(figsize=(width / 100, height / 100))
    if not df.empty:
        df.plot(ax=plt.gca())
    plt.title("CPI Year over Year")
    plt.ylabel("%")
    plt.xlabel("")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
