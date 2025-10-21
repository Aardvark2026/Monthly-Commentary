from pathlib import Path
import sys

md = Path("commentary/out/monthly_commentary.md").read_text(encoding="utf-8")

checks = [
    ("No 'n/a'", lambda s: "n/a" not in s.lower()),
    ("Has all headings", lambda s: all(h in s for h in [
        "Government Bond Yields (10-Year)",
        "Inflation (CPI YoY)", "Policy", "Equities", "FX", "Commodities"
    ])),
    ("Minimum length 250 words", lambda s: len(s.split()) >= 250),
]
fails = [name for name, fn in checks if not fn(md)]
if fails:
    sys.exit("QUALITY FAIL: " + ", ".join(fails))