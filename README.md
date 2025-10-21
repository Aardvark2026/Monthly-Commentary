# Monthly Commentary

Automated scaffolding for generating monthly market commentary across US and Australian markets. The tool fetches macro and market data, assembles commentary text, exports client-ready artefacts, and produces charts suitable for reporting or publishing via GitHub Pages.

## Features

- Government bond yields (US and Australia, 10-year)
- Inflation (CPI YoY) for US (FRED) and Australia (ABS)
- Policy rates (Fed funds and RBA cash rate)
- Equities (S&P 500, ASX 200)
- FX (AUDUSD and UUP as a DXY proxy)
- Commodities (Gold, WTI, Brent, Iron ore with TradingEconomics fallback)
- Markdown commentary, Excel dashboard, PNG charts, and JSON snapshots per month
- Optional tiny LLM support via `llama_cpp` with a rule-based fallback
- GitHub Actions workflow for scheduled generation and GitHub Pages publication

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Generate the latest monthly package

```bash
python -m src.cli --month auto --markets us,au --outputs md,xlsx
```

Command options:

- `--month`: `YYYY-MM` or `auto` (previous full month)
- `--markets`: comma-separated market codes (`us`, `au`)
- `--outputs`: subset of `md`, `xlsx`
- `--lookback`: history length in months (default 24)
- `--verbose`: enable debug logging

Outputs are written to `reports/<YYYY-MM>/` with sub-folders for charts and snapshots.

### Enabling the tiny LLM (optional)

1. Install [`llama_cpp_python`](https://pypi.org/project/llama-cpp-python/)
2. Set `DOWNLOAD_TINY_LLM=1` before running the CLI to auto-download the TinyLlama GGUF model

If the model or binary is unavailable, the generator falls back to deterministic copy suitable for client distribution.

## GitHub Actions

The workflow `.github/workflows/monthly-commentary.yml` runs on-demand or on the 1st of each month at 06:00 UTC. It:

1. Installs dependencies
2. Generates the monthly package via the CLI
3. Uploads run artefacts
4. Publishes the `reports/` directory to GitHub Pages

An email job is scaffolded but disabled pending SMTP credentials.
