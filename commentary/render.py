import json
from pathlib import Path
import pandas as pd, matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader
from analysis import analyze
from summarise import to_paragraphs, SYSTEM_STYLE, PROMPT_TEMPLATE
import subprocess, os

def charts(data):
    out = Path("commentary/out/charts")
    out.mkdir(parents=True, exist_ok=True)

    # 10y history
    bonds = data['bonds']['history'].tail(12)
    plt.figure()
    plt.plot(bonds['date'], bonds['us10y'], label="US 10y")
    plt.plot(bonds['date'], bonds['au10y'], label="AU 10y")
    plt.title("10-Year Government Yields (last 12m)")
    plt.legend(); plt.tight_layout()
    plt.savefig(out / "tenors_10y.png"); plt.close()

    # CPI
    cpi = data['cpi']['history'].tail(12)
    plt.figure()
    plt.plot(cpi['date'], cpi['us_cpi_yoy'], label="US CPI YoY")
    plt.plot(cpi['date'], cpi['au_cpi_yoy'], label="AU CPI YoY")
    plt.title("CPI YoY (last 12m)")
    plt.legend(); plt.tight_layout()
    plt.savefig(out / "cpi.png"); plt.close()

    # MoM bars
    eq = data['equities']['history'].tail(1)
    fx = data['fx']['history'].tail(1)
    com = data['commodities_history'].tail(1)
    bars = {
        'S&P 500': float(eq['spx_mom'].iloc[-1]) if len(eq) else 0.0,
        'ASX 200': float(eq['asx200_mom'].iloc[-1]) if len(eq) else 0.0,
        'AUDUSD': float(fx['audusd_mom'].iloc[-1]) if len(fx) else 0.0,
        'DXY': float(fx['dxy_mom'].iloc[-1]) if len(fx) else 0.0,
        'Gold': float(com['gold_mom'].iloc[-1]) if len(com) else 0.0,
        'WTI': float(com['wti_mom'].iloc[-1]) if len(com) else 0.0,
        'Brent': float(com['brent_mom'].iloc[-1]) if len(com) else 0.0,
        'Iron ore': float(com['iron_ore_mom'].iloc[-1]) if len(com) else 0.0,
    }
    plt.figure()
    plt.bar(list(bars.keys()), list(bars.values()))
    plt.title("MoM Moves (latest month)")
    plt.xticks(rotation=45, ha='right'); plt.tight_layout()
    plt.savefig(out / "mom_bars.png"); plt.close()

def write_excel(data):
    outp = Path("commentary/out/dashboard.xlsx")
    with pd.ExcelWriter(outp, engine="xlsxwriter") as xw:
        data['bonds']['history'].to_excel(xw, sheet_name="Bonds", index=False)
        data['cpi']['history'].to_excel(xw, sheet_name="CPI", index=False)
        data['equities']['history'].to_excel(xw, sheet_name="Equities", index=False)
        data['fx']['history'].to_excel(xw, sheet_name="FX", index=False)
        data['commodities_history'].to_excel(xw, sheet_name="Commodities", index=False)
        pd.DataFrame([{
            "us10y_last": data['bonds']['us10y']['last'],
            "us10y_mom_pct": data['bonds']['us10y']['mom_pct'],
            "au10y_last": data['bonds']['au10y']['last'],
            "au10y_mom_pct": data['bonds']['au10y']['mom_pct']
        }]).to_excel(xw, sheet_name="Summary", index=False)

def llm_prose(data, month):
    user = PROMPT_TEMPLATE.format(month=month, json=json.dumps(data))
    system = SYSTEM_STYLE
    model_path = "commentary/models/model.gguf"
    res = subprocess.check_output([
        "python","commentary/scripts/run_llm.py",
        system, user, model_path
    ], text=True)
    # crude split into sections if model returns big text; else we wrap everything into dict
    # For safety, just return a dict with single chunk repeated per section
    text = res.strip()
    return {
        'bonds': text,
        'cpi': text,
        'policy': text,
        'equities': text,
        'fx': text,
        'commodities': text
    }

def main(month="2025-09", use_llm=True):
    dat = analyze()
    charts(dat)
    write_excel(dat)
    # prose
    prose = llm_prose(dat, month) if use_llm else __import__("summarise").to_paragraphs(dat)

    env = Environment(loader=FileSystemLoader("commentary/templates"))
    tmpl = env.get_template("monthly.md.j2")
    md = tmpl.render(
        month=month,
        us10y=dat['bonds']['us10y'],
        au10y=dat['bonds']['au10y'],
        cpi=dat['cpi'],
        equities=dat['equities'],
        fx=dat['fx'],
        commodities=dat['commodities'],
        policy=dat['policy'],
        prose=prose
    )
    Path("commentary/out").mkdir(exist_ok=True, parents=True)
    Path("commentary/out/monthly_commentary.md").write_text(md, encoding="utf-8")

if __name__ == "__main__":
    main()