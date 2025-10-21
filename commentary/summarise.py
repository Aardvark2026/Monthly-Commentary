def arrow(x):
    if x is None: return ''
    return '↑' if x > 0 else '↓' if x < 0 else '→'

def bond_sentence(level, mom):
    if level is None: return "10-year data not available this month and will be updated next release."
    if mom is None: return f"10-year yields ended the month at {level:.2f}%."
    sign = "fell" if mom < 0 else "rose" if mom > 0 else "were little changed"
    return f"10-year yields {sign} to {level:.2f}% ({arrow(mom)} {abs(mom):.2f}% m/m)."

def to_paragraphs(d):
    return {
        'bonds': bond_sentence(d['bonds']['us10y']['last'], d['bonds']['us10y']['mom_pct']),
        'cpi': (f"US CPI YoY stands at {d['cpi']['us']:.2f}%, with Australia at {d['cpi']['au']:.2f}%."
                if d['cpi']['us'] is not None and d['cpi']['au'] is not None
                else "CPI YoY data not available for all regions this month."),
        'policy': (f"Fed funds at {d['policy']['fed']:.3g}% and RBA cash rate at {d['policy']['rba']:.3g}%."
                   if d['policy']['fed'] is not None and d['policy']['rba'] is not None
                   else "Policy rates data not available this month."),
        'equities': (f"S&P 500 {d['equities']['spx_mom']:.2f}% m/m; ASX 200 {d['equities']['asx_mom']:.2f}% m/m."
                     if d['equities']['spx_mom'] is not None and d['equities']['asx_mom'] is not None
                     else "Equities performance not fully available this month."),
        'fx': (f"AUDUSD {d['fx']['audusd_mom']:.2f}% m/m; DXY {d['fx']['dxy_mom']:.2f}% m/m."
               if d['fx']['audusd_mom'] is not None and d['fx']['dxy_mom'] is not None
               else "FX data not fully available this month."),
        'commodities': ("Gold {0:.2f}% m/m; WTI {1:.2f}%; Brent {2:.2f}%; Iron ore {3:.2f}%."
                        .format(d['commodities'].get('gold_mom', float('nan')),
                                d['commodities'].get('wti_mom', float('nan')),
                                d['commodities'].get('brent_mom', float('nan')),
                                d['commodities'].get('iron_ore_mom', float('nan')))
                        if d['commodities'].get('gold_mom') is not None
                        else "Commodities data not fully available this month.")
    }

SYSTEM_STYLE = """You are a financial editor. Style: concise, client-friendly, no hype or slang.
For each section write 2–4 sentences: 1) Key move 2) Drivers 3) Why it matters 4) Implications.
If any metric missing, state 'Data not available this month and will be updated next release.' Avoid bullet points.
"""

PROMPT_TEMPLATE = """Write the Monthly Commentary for {month} using ONLY this JSON:

{json}

Sections and order (exact headings): 
- Government Bond Yields (10-Year), Inflation (CPI YoY), Policy, Equities, FX, Commodities.

Constraints:
- Use the numbers directly; do not make up data. Reference MoM and YoY where present.
- Keep tone professional and brief.
"""