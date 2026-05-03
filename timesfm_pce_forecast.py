# timesfm_pce_forecast
# # TimesFM PCE Hybrid Forecasting Pipeline
# 
# ## Phase 0 One-time environment setup (run in terminal, not here)
# 
# ```powershell
# # From G:\Coding\For Work\BUOD\Brent_simulation\TimesFM
# python -m venv .venv
# .venv\Scripts\Activate.ps1
# pip install pandas matplotlib fredapi pytest pytest-cov ipykernel jupyter nbformat
# 
# # TimesFM installation (downloads ~500 MB from HuggingFace â€” do this once):
# pip install timesfm[xreg]
# 
# # Register kernel
# python -m ipykernel install --user --name=timesfm-env --display-name "Python (timesfm-env)"
# ```
# 
# After installation select kernel **"Python (timesfm-env)"** in the kernel picker above.
# 

# %%
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


# %% [markdown]
# ## Phase 1 Data Acquisition

# %%
CSV_PATH = PROJECT_ROOT / "Section2All_xls - U20304-M.csv"
pce_df = parse_dreqrg_csv(CSV_PATH)
print(f"PCE series loaded: {len(pce_df)} months, "
      f"{pce_df['Date'].iloc[0].strftime('%Y-%m')} to "
      f"{pce_df['Date'].iloc[-1].strftime('%Y-%m')}")
print(pce_df.head(3))
print(pce_df.tail(3))


# %%
# Get a free API key at https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY = "4840f2b6d06620ecc858b373a4669c43"
brent_df = fetch_brent_crude(FRED_API_KEY)
print(f"Brent Crude loaded: {len(brent_df)} months, "
      f"{brent_df['Date'].iloc[0].strftime('%Y-%m')} to "
      f"{brent_df['Date'].iloc[-1].strftime('%Y-%m')}")
print(brent_df.tail(3))


# %%
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
ax1.set_title("DREQRG PCE Index vs. Brent Crude Oil â€” Historical")
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax1.xaxis.set_major_locator(mdates.YearLocator(5))

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

plt.tight_layout()
plt.show()


# %% [markdown]
# ## Phase 2 Qualitative Scenario Generation (Gemini)
# 
# **Copy the prompt below, paste it into [gemini.google.com](https://gemini.google.com), then paste the output into Cell 6.**
# 
# ---
# 
# > **PROMPT TO PASTE INTO GEMINI:**
# >
# > You are a macroeconomic analyst specializing in energy markets and consumer spending. Your task is to generate three 13-month forward trajectories for Brent Crude oil prices (May 2026 through May 2027 inclusive), calibrated against specific historical macro regimes.
# >
# > **Historical Regime Context (for elasticity calibration):**
# > - **2007 - 2008 (Demand Shock):** Brent peaked >$140/bbl in a booming global economy, then collapsed with the GFC. Tech spending was high until the credit freeze caused sudden demand destruction. Elasticity pattern: gradual rise â†’ sharp peak â†’ collapse.
# > - **2010 - 2011 (Arab Spring / Supply Shock):** Brent spiked past $120/bbl due to Middle East instability + Tohoku earthquake crippling semiconductor/photographic supply chains. Price increases driven by product scarcity, not just energy. Elasticity pattern: step-up plateau with elevated volatility.
# > - **2021 - 2022 (Post-Pandemic / Ukraine War):** Oil spiked amid Russia-Ukraine conflict and global reopening. Energy acted as a multiplier on existing supply chain paralysis and chip shortages. Elasticity pattern: persistent elevated baseline with a single sharp spike.
# >
# > **Your Task:**
# > 1. Briefly assess the current geopolitical and macroeconomic landscape as of May 2026 (include: active conflicts, OPEC+ posture, global growth trajectory, any major supply chain disruptions).
# > 2. Identify which historical regime (or blend) best maps to today's reality. Justify in 2-3 sentences.
# > 3. Generate exactly **three named scenarios** as Python lists of 13 monthly Brent Crude price values (USD/bbl), covering May 2026 through May 2027:
# >    - `base_case`: Highest-probability path based on current consensus and the matched historical elasticity.
# >    - `bull_case`: Severe upside shock (e.g., rapid conflict escalation, major supply disruption).
# >    - `bear_case`: Downside scenario (e.g., global recession signal, unexpected supply glut, OPEC+ collapse).
# >
# > **Output format return exactly this Python block:**
# > ```python
# > base_case = [X, X, X, X, X, X, X, X, X, X, X, X, X]   # May 2026 â€“ May 2027
# > bull_case = [X, X, X, X, X, X, X, X, X, X, X, X, X]
# > bear_case = [X, X, X, X, X, X, X, X, X, X, X, X, X]
# > narrative = """
# > [2-3 sentence justification of the analog match and key assumptions]
# > """
# > ```
# 

# %%
base_case = [118.0, 121.0, 119.0, 122.0, 118.0, 115.0, 117.0, 114.0, 112.0, 110.0, 111.0, 108.0, 105.0]   # May 2026 – May 2027
bull_case = [120.0, 135.0, 145.0, 150.0, 148.0, 142.0, 145.0, 138.0, 135.0, 140.0, 138.0, 135.0, 130.0]
bear_case = [115.0, 95.0, 85.0, 80.0, 78.0, 75.0, 70.0, 68.0, 65.0, 65.0, 62.0, 60.0, 58.0]
narrative = """
As of May 2026, energy markets are reeling from the U.S.-Israel-Iran conflict and the resulting closure of the Strait of Hormuz (pushing Brent near $118/bbl), coupled with the UAE's sudden May 1 exit from OPEC+ to monetize its massive spare capacity. This landscape best maps to the 2010–2011 Arab Spring supply shock regime, which was characterized by a step-up plateau and elevated volatility. The physical product scarcity created by the Hormuz blockade establishes a persistently high structural baseline, while the threat of an unrestrained UAE flooding the market once shipping lanes reopen injects immense forward-looking volatility.
"""

forecast_dates = make_forecast_dates()
validate_scenarios(base_case, bull_case, bear_case)

print("Scenarios validated OK")
print(f"Forecast window: {forecast_dates[0].strftime('%Y-%m')} to {forecast_dates[-1].strftime('%Y-%m')}")
print("Narrative:", narrative.strip())
print("Base Case ($/bbl):", base_case)


# %% [markdown]
# ## Phase 3 TimesFM Quantitative Forecasting

# %%
import timesfm

# TimesFM 2.5 API: from_pretrained() replaces TimesFm/TimesFmHparams/TimesFmCheckpoint.
# First run downloads ~500 MB from HuggingFace — subsequent runs use local cache.
# return_backcast=True is required to use forecast_with_covariates.
tfm = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
    "google/timesfm-2.5-200m-pytorch"
)
tfm.compile(
    timesfm.ForecastConfig(
        max_context=1024,
        max_horizon=256,
        normalize_inputs=True,
        return_backcast=True,
    )
)
print("TimesFM model initialized and compiled")


# %%
import numpy as np

scenarios = {
    "base": base_case,
    "bull": bull_case,
    "bear": bear_case,
}
forecasts = {}

for name, scenario in scenarios.items():
    history_df = build_history_payload(merged_df, context_len=120)

    # TimesFM 2.5 takes numpy arrays, not DataFrames.
    pce_context = history_df["y"].to_numpy()               # shape: (120,)
    brent_context = history_df["Brent_Crude"].to_numpy()   # shape: (120,)
    brent_future = np.array(scenario, dtype=float)          # shape: (13,)

    # Dynamic covariate must cover context + horizon.
    # Horizon is inferred as len(combined) - len(input) = 133 - 120 = 13.
    brent_combined = np.concatenate([brent_context, brent_future])  # shape: (133,)

    point_fc, _ = tfm.forecast_with_covariates(
        inputs=[pce_context],
        dynamic_numerical_covariates={"Brent_Crude": [brent_combined]},
        xreg_mode="xreg + timesfm",
        normalize_xreg_target_per_input=True,
    )
    # point_fc shape: (1, horizon) — slice to 13 steps
    forecasts[name] = point_fc[0][:13]
    print(f"{name}: {forecasts[name]}")

print("All forecasts complete. NaN check:",
      {k: int(pd.isna(v).sum()) for k, v in forecasts.items()})


# %% [markdown]
# ## Phase 4 Visualization

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Historical window: last 12 years for readability
history_start = pd.Timestamp("2014-01-01")

brent_hist = brent_df[brent_df["Date"] >= history_start]
pce_hist   = pce_df[pce_df["Date"] >= history_start]
last_brent_obs = pd.Timestamp("2026-04-01")
last_pce_obs   = pd.Timestamp("2026-02-01")

scenario_styles = {
    "base": ("steelblue", "solid", "Base case"),
    "bull": ("firebrick", "dash", "Bull case (high oil)"),
    "bear": ("seagreen", "dash", "Bear case (low oil)"),
}
pce_scenario_styles = {
    "base": ("darkorange", "solid", "Base case"),
    "bull": ("crimson", "dash", "Bull case (high oil)"),
    "bear": ("goldenrod", "dash", "Bear case (low oil)"),
}
brent_scenarios = {"base": base_case, "bull": bull_case, "bear": bear_case}

fig = make_subplots(specs=[[{"secondary_y": True}]])

# Connect historical lines to forecast lines
fc_dates_brent = [last_brent_obs] + list(forecast_dates)
fc_dates_pce = [last_pce_obs] + list(forecast_dates)

# ── Brent Crude (Primary Y-Axis) ───────────────────────────────────────────
fig.add_trace(go.Scatter(x=brent_hist["Date"], y=brent_hist["Brent_Crude"],
                         mode='lines', line=dict(color='black', width=2),
                         name="Brent Crude (historical)"), secondary_y=False)

# Add uncertainty band (bear-bull) for Brent
fig.add_trace(go.Scatter(
    x=fc_dates_brent + fc_dates_brent[::-1],
    y=[brent_hist["Brent_Crude"].iloc[-1]] + list(brent_scenarios["bull"]) + list(brent_scenarios["bear"])[::-1] + [brent_hist["Brent_Crude"].iloc[-1]],
    fill='toself',
    fillcolor='rgba(176,196,222,0.4)',  # lightsteelblue with alpha
    line=dict(color='rgba(255,255,255,0)'),
    hoverinfo="skip",
    showlegend=True,
    name="Brent Uncertainty (bear–bull)"
), secondary_y=False)

for name, (color, dash, label) in scenario_styles.items():
    connected_y = [brent_hist["Brent_Crude"].iloc[-1]] + list(brent_scenarios[name])
    fig.add_trace(go.Scatter(x=fc_dates_brent, y=connected_y,
                             mode='lines', line=dict(color=color, width=2, dash=dash),
                             name=f"Brent {label}"), secondary_y=False)

# ── PCE Index (Secondary Y-Axis) ──────────────────────────────────────────
fig.add_trace(go.Scatter(x=pce_hist["Date"], y=pce_hist["PCE_Index"],
                         mode='lines', line=dict(color='purple', width=2),
                         name="DREQRG PCE Index (historical)"), secondary_y=True)

# Add uncertainty band (bear-bull) for PCE
fig.add_trace(go.Scatter(
    x=fc_dates_pce + fc_dates_pce[::-1],
    y=[pce_hist["PCE_Index"].iloc[-1]] + list(forecasts["bull"]) + list(forecasts["bear"])[::-1] + [pce_hist["PCE_Index"].iloc[-1]],
    fill='toself',
    fillcolor='rgba(218,112,214,0.3)',  # orchid with alpha
    line=dict(color='rgba(255,255,255,0)'),
    hoverinfo="skip",
    showlegend=True,
    name="PCE Uncertainty (bear–bull)"
), secondary_y=True)

for name, (color, dash, label) in pce_scenario_styles.items():
    connected_y = [pce_hist["PCE_Index"].iloc[-1]] + list(forecasts[name])
    fig.add_trace(go.Scatter(x=fc_dates_pce, y=connected_y,
                             mode='lines', line=dict(color=color, width=2, dash=dash),
                             name=f"PCE {label}"), secondary_y=True)

fig.add_vline(x=last_brent_obs.strftime('%Y-%m-%d'), line_width=1.5, line_dash="dash", line_color="gray", 
              annotation_text="Last Brent obs", annotation_position="top left")
fig.add_vline(x=last_pce_obs.strftime('%Y-%m-%d'), line_width=1.5, line_dash="dot", line_color="gray", 
              annotation_text="Last PCE obs", annotation_position="bottom right")

fig.update_yaxes(title_text="Brent Crude (USD/bbl)", secondary_y=False)
fig.update_yaxes(title_text="PCE Price Index (2017=100)", secondary_y=True, showgrid=False)
fig.update_layout(height=800, width=1200, hovermode="x unified", 
                  title_text="Interactive Forecast Dashboard: Brent & PCE in One Chart",
                  legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))

fig.write_html("dreqrg_forecast_fan_chart.html")
fig.show()
print("Interactive chart saved to dreqrg_forecast_fan_chart.html and opened in browser.")



