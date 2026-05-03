"""
build_notebook.py — generates timesfm_pce_forecast.ipynb using nbformat.
Run once: python build_notebook.py
"""
import nbformat

nb = nbformat.v4.new_notebook()
nb.metadata["kernelspec"] = {
    "display_name": "Python (timesfm-env)",
    "language": "python",
    "name": "timesfm-env",
}
nb.metadata["language_info"] = {"name": "python", "version": "3.13"}

cells = []

# ── Phase 0 setup note ──────────────────────────────────────────────────────
cells.append(nbformat.v4.new_markdown_cell("""\
# TimesFM PCE Hybrid Forecasting Pipeline

## Phase 0 — One-time environment setup (run in terminal, not here)

```powershell
# From G:\\Coding\\For Work\\BUOD\\Brent_simulation\\TimesFM
python -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install pandas matplotlib fredapi pytest pytest-cov ipykernel jupyter nbformat

# TimesFM installation (downloads ~500 MB from HuggingFace — do this once):
pip install timesfm

# Register kernel
python -m ipykernel install --user --name=timesfm-env --display-name "Python (timesfm-env)"
```

After installation select kernel **"Python (timesfm-env)"** in the kernel picker above.
"""))

# ── Cell 1: Imports + sys.path bootstrap ───────────────────────────────────
cells.append(nbformat.v4.new_code_cell("""\
import sys
from pathlib import Path

# Make pipeline.py importable from the project root
PROJECT_ROOT = Path().resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from getpass import getpass
from pipeline import (
    parse_dreqrg_csv,
    fetch_brent_crude,
    merge_pce_brent,
    validate_scenarios,
    make_forecast_dates,
    build_history_payload,
    build_future_payload,
)

print("Pipeline module loaded OK")
"""))

# ── Cell 2: Parse DREQRG CSV ───────────────────────────────────────────────
cells.append(nbformat.v4.new_markdown_cell("## Phase 1 — Data Acquisition"))
cells.append(nbformat.v4.new_code_cell("""\
CSV_PATH = PROJECT_ROOT / "Section2All_xls - U20304-M.csv"
pce_df = parse_dreqrg_csv(CSV_PATH)
print(f"PCE series loaded: {len(pce_df)} months, "
      f"{pce_df['Date'].iloc[0].strftime('%Y-%m')} to "
      f"{pce_df['Date'].iloc[-1].strftime('%Y-%m')}")
display(pce_df.head(3))
display(pce_df.tail(3))
"""))

# ── Cell 3: Fetch Brent Crude from FRED ───────────────────────────────────
cells.append(nbformat.v4.new_code_cell("""\
# Get a free API key at https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY = getpass("Paste your FRED API key: ")
brent_df = fetch_brent_crude(FRED_API_KEY)
print(f"Brent Crude loaded: {len(brent_df)} months, "
      f"{brent_df['Date'].iloc[0].strftime('%Y-%m')} to "
      f"{brent_df['Date'].iloc[-1].strftime('%Y-%m')}")
display(brent_df.tail(3))
"""))

# ── Cell 4: Merge & sanity plot ─────────────────────────────────────────────
cells.append(nbformat.v4.new_code_cell("""\
merged_df = merge_pce_brent(pce_df, brent_df)
print(f"Merged dataset: {len(merged_df)} months, "
      f"{merged_df['Date'].iloc[0].strftime('%Y-%m')} to "
      f"{merged_df['Date'].iloc[-1].strftime('%Y-%m')}")

fig, ax1 = plt.subplots(figsize=(14, 5))
ax2 = ax1.twinx()

ax1.plot(merged_df["Date"], merged_df["PCE_Index"], color="steelblue", label="PCE Index (DREQRG)")
ax2.plot(merged_df["Date"], merged_df["Brent_Crude"], color="darkorange", alpha=0.7, label="Brent Crude ($/bbl)")

ax1.set_ylabel("PCE Price Index (2017=100)", color="steelblue")
ax2.set_ylabel("Brent Crude (USD/bbl)", color="darkorange")
ax1.set_xlabel("Date")
ax1.set_title("DREQRG PCE Index vs. Brent Crude Oil — Historical")
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax1.xaxis.set_major_locator(mdates.YearLocator(5))

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

plt.tight_layout()
plt.show()
"""))

# ── Cell 5: Gemini prompt (markdown, display-only) ─────────────────────────
cells.append(nbformat.v4.new_markdown_cell("""\
## Phase 2 — Qualitative Scenario Generation (Gemini)

**Copy the prompt below, paste it into [gemini.google.com](https://gemini.google.com), then paste the output into Cell 6.**

---

> **PROMPT TO PASTE INTO GEMINI:**
>
> You are a macroeconomic analyst specializing in energy markets and consumer spending. Your task is to generate three 13-month forward trajectories for Brent Crude oil prices (May 2026 through May 2027 inclusive), calibrated against specific historical macro regimes.
>
> **Historical Regime Context (for elasticity calibration):**
> - **2007–2008 (Demand Shock):** Brent peaked >$140/bbl in a booming global economy, then collapsed with the GFC. Tech spending was high until the credit freeze caused sudden demand destruction. Elasticity pattern: gradual rise → sharp peak → collapse.
> - **2010–2011 (Arab Spring / Supply Shock):** Brent spiked past $120/bbl due to Middle East instability + Tohoku earthquake crippling semiconductor/photographic supply chains. Price increases driven by product scarcity, not just energy. Elasticity pattern: step-up plateau with elevated volatility.
> - **2021–2022 (Post-Pandemic / Ukraine War):** Oil spiked amid Russia-Ukraine conflict and global reopening. Energy acted as a multiplier on existing supply chain paralysis and chip shortages. Elasticity pattern: persistent elevated baseline with a single sharp spike.
>
> **Your Task:**
> 1. Briefly assess the current geopolitical and macroeconomic landscape as of May 2026 (include: active conflicts, OPEC+ posture, global growth trajectory, any major supply chain disruptions).
> 2. Identify which historical regime (or blend) best maps to today's reality. Justify in 2-3 sentences.
> 3. Generate exactly **three named scenarios** as Python lists of 13 monthly Brent Crude price values (USD/bbl), covering May 2026 through May 2027:
>    - `base_case`: Highest-probability path based on current consensus and the matched historical elasticity.
>    - `bull_case`: Severe upside shock (e.g., rapid conflict escalation, major supply disruption).
>    - `bear_case`: Downside scenario (e.g., global recession signal, unexpected supply glut, OPEC+ collapse).
>
> **Output format — return exactly this Python block:**
> ```python
> base_case = [X, X, X, X, X, X, X, X, X, X, X, X, X]   # May 2026 – May 2027
> bull_case = [X, X, X, X, X, X, X, X, X, X, X, X, X]
> bear_case = [X, X, X, X, X, X, X, X, X, X, X, X, X]
> narrative = \"\"\"
> [2-3 sentence justification of the analog match and key assumptions]
> \"\"\"
> ```
"""))

# ── Cell 6: Gemini output paste target ─────────────────────────────────────
cells.append(nbformat.v4.new_code_cell("""\
# ── PASTE GEMINI OUTPUT BELOW THIS LINE ──────────────────────────────────
base_case = [75, 77, 79, 81, 80, 78, 76, 74, 73, 72, 71, 70, 69]   # placeholder
bull_case = [80, 85, 92, 100, 105, 110, 108, 103, 98, 94, 90, 87, 85]  # placeholder
bear_case = [72, 68, 65, 62, 60, 58, 56, 55, 54, 53, 52, 51, 50]   # placeholder
narrative = \"\"\"
PLACEHOLDER — replace with Gemini narrative.
These values are illustrative; paste the actual Gemini output above before running Cell 8.
\"\"\"
# ── END PASTE REGION ────────────────────────────────────────────────────────

forecast_dates = make_forecast_dates()
validate_scenarios(base_case, bull_case, bear_case)

print("Scenarios validated OK")
print(f"Forecast window: {forecast_dates[0].strftime('%Y-%m')} to {forecast_dates[-1].strftime('%Y-%m')}")
print("Narrative:", narrative.strip())
print("Base Case ($/bbl):", base_case)
"""))

# ── Cell 7: TimesFM initialization ─────────────────────────────────────────
cells.append(nbformat.v4.new_markdown_cell("## Phase 3 — TimesFM Quantitative Forecasting"))
cells.append(nbformat.v4.new_code_cell("""\
import timesfm

# First run downloads ~500 MB from HuggingFace — subsequent runs use local cache.
# Change backend to "gpu" if CUDA is available.
tfm = timesfm.TimesFm(
    hparams=timesfm.TimesFmHparams(
        backend="cpu",
        horizon_len=13,
        context_len=120,
    ),
    checkpoint=timesfm.TimesFmCheckpoint(
        huggingface_repo_id="google/timesfm-2.0-500m-pytorch",
    ),
)
print("TimesFM model initialized")
# Uncomment to inspect the forecast_on_df signature:
# help(tfm.forecast_on_df)
"""))

# ── Cell 8: Build payloads & run forecasts ─────────────────────────────────
cells.append(nbformat.v4.new_code_cell("""\
scenarios = {
    "base": base_case,
    "bull": bull_case,
    "bear": bear_case,
}
forecasts = {}

for name, scenario in scenarios.items():
    history_df = build_history_payload(merged_df, context_len=120)
    future_df = build_future_payload(scenario, forecast_dates)

    forecast_df = tfm.forecast_on_df(
        inputs=history_df,
        freq="MS",
        value_name="y",
        dynamic_numerical_covariates=["Brent_Crude"],
        dynamic_numerical_covariate_future=future_df,
    )
    # Extract point forecast (TimesFM 2.0 returns column "timesfm")
    point_col = [c for c in forecast_df.columns if "timesfm" in c.lower()][0]
    forecasts[name] = forecast_df[point_col].values
    print(f"{name}: {forecasts[name]}")

print("\\nAll forecasts complete. NaN check:",
      {k: int(pd.isna(v).sum()) for k, v in forecasts.items()})
"""))

# ── Cell 9: Fan chart ───────────────────────────────────────────────────────
cells.append(nbformat.v4.new_markdown_cell("## Phase 4 — Visualization"))
cells.append(nbformat.v4.new_code_cell("""\
# Historical window: last 12 years for readability
history_start = pd.Timestamp("2014-01-01")
hist_plot = merged_df[merged_df["Date"] >= history_start]
last_obs = pd.Timestamp("2026-04-01")

fig, ax = plt.subplots(figsize=(15, 6))

# Historical PCE
ax.plot(hist_plot["Date"], hist_plot["PCE_Index"],
        color="black", linewidth=2, label="DREQRG PCE Index (historical)")

# Vertical separator
ax.axvline(last_obs, color="gray", linestyle="--", linewidth=1.2, label="Last observed (Apr 2026)")

# Forecast lines
ax.plot(forecast_dates, forecasts["base"],
        color="steelblue", linewidth=2, label="Base case")
ax.plot(forecast_dates, forecasts["bull"],
        color="firebrick", linewidth=1.8, linestyle="--", label="Bull case (high oil)")
ax.plot(forecast_dates, forecasts["bear"],
        color="seagreen", linewidth=1.8, linestyle="--", label="Bear case (low oil)")

# Uncertainty band
ax.fill_between(forecast_dates, forecasts["bear"], forecasts["bull"],
                color="lightgray", alpha=0.4, label="Uncertainty band (bear–bull)")

ax.set_title("DREQRG PCE Index Forecast — Brent Crude Oil Scenarios", fontsize=14)
ax.set_xlabel("Date")
ax.set_ylabel("PCE Price Index (2017=100)")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")
ax.legend(loc="upper left")
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("dreqrg_forecast_fan_chart.png", dpi=150)
plt.show()
print("Chart saved to dreqrg_forecast_fan_chart.png")
"""))

nb.cells = cells

output_path = "G:/Coding/For Work/BUOD/Brent_simulation/TimesFM/timesfm_pce_forecast.ipynb"
with open(output_path, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print(f"Notebook written to: {output_path}")
