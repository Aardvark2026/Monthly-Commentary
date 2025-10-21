import pandas as pd, numpy as np
from dateutil.relativedelta import relativedelta

def pct_change(curr, prev):
    if pd.isna(curr) or pd.isna(prev) or prev == 0:
        return None
    return (curr/prev - 1) * 100.0

def load_series(path, cols):
    df = pd.read_csv(path, parse_dates=['date']).sort_values('date')
    return df[['date', *cols]]

def last_and_mom(df, col):
    if len(df) < 2: return None, None
    curr = float(df[col].iloc[-1])
    prev = float(df[col].iloc[-2])
    return curr, pct_change(curr, prev)

def analyze():
    out = {}

    bonds = load_series('commentary/data/bonds.csv', ['us10y','au10y'])
    us10_now, us10_mom = last_and_mom(bonds, 'us10y')
    au10_now, au10_mom = last_and_mom(bonds, 'au10y')
    out['bonds'] = {'us10y': {'last': us10_now, 'mom_pct': us10_mom},
                    'au10y': {'last': au10_now, 'mom_pct': au10_mom},
                    'history': bonds.tail(12)}

    cpi = load_series('commentary/data/cpi.csv', ['us_cpi_yoy','au_cpi_yoy'])
    out['cpi'] = {'us': float(cpi['us_cpi_yoy'].iloc[-1]) if len(cpi) else None,
                  'au': float(cpi['au_cpi_yoy'].iloc[-1]) if len(cpi) else None,
                  'history': cpi.tail(12)}

    eq = load_series('commentary/data/equities.csv', ['spx_mom','asx200_mom'])
    out['equities'] = {'spx_mom': float(eq['spx_mom'].iloc[-1]) if len(eq) else None,
                       'asx_mom': float(eq['asx200_mom'].iloc[-1]) if len(eq) else None,
                       'history': eq.tail(12)}

    fx = load_series('commentary/data/fx.csv', ['audusd_mom','dxy_mom'])
    out['fx'] = {'audusd_mom': float(fx['audusd_mom'].iloc[-1]) if len(fx) else None,
                 'dxy_mom': float(fx['dxy_mom'].iloc[-1]) if len(fx) else None,
                 'history': fx.tail(12)}

    com = load_series('commentary/data/commodities.csv', ['gold_mom','wti_mom','brent_mom','iron_ore_mom'])
    out['commodities'] = {k: float(com[k].iloc[-1]) if k in com else None for k in com.columns if k!='date'}
    out['commodities_history'] = com.tail(12)

    pol = load_series('commentary/data/policy.csv',['fed_rate','rba_rate'])
    out['policy'] = {'fed': float(pol['fed_rate'].iloc[-1]) if len(pol) else None,
                     'rba': float(pol['rba_rate'].iloc[-1]) if len(pol) else None,
                     'history': pol.tail(12)}

    # Simple required checks list — quality.py enforces
    out['required'] = {
        'us10y_last': us10_now, 'au10y_last': au10_now,
        'us_cpi': out['cpi']['us'], 'au_cpi': out['cpi']['au'],
        'spx_mom': out['equities']['spx_mom'], 'asx_mom': out['equities']['asx_mom'],
        'audusd_mom': out['fx']['audusd_mom'], 'dxy_mom': out['fx']['dxy_mom'],
        'gold_mom': out['commodities'].get('gold_mom')
    }
    return out

if __name__ == "__main__":
    print(analyze())