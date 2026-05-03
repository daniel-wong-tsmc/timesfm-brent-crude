## 1. What are we trying to accomplish? (Objective & Scope)
**Objective:** 
To architect and deploy a 12-month hybrid forecasting pipeline that predicts the Personal Consumption Expenditures (PCE) Index for the "video, audio, photographic, and information processing equipment and media" sector (represented by BEA Series `DREQRG`). 

**Target Audience:**
The end-users are business analysts who oversee overall macroeconomic trends. They are domain-literate in economics but are deep learning engineers. The final tools and outputs (specifically the Phase 4 dashboard) must be intuitive, narrative-driven, and clearly link macroeconomic scenarios to the forecast data without hiding behind black-box machine learning jargon.

**Scope:**
The system will generate forecasts from May 2026 through May 2027. Instead of relying solely on historical pattern recognition, the forecast will actively incorporate forward-looking geopolitical and macroeconomic realities by using the price of Brent Crude oil.

**Non-Goals:**
*   We are not building a causal inference model to explain *why* oil impacted electronics in 2008.
*   We are not attempting to build an algorithmic trading bot for oil futures. 

**Expected Deliverables:**
*   A single chart that displays the historical PCE index and the forecast for the next 12 months.
*   The chart should also display the historical Brent Crude index and the forecast for the next 12 months.

## 2. Why are we doing it? (Problem & Value Proposition)
**The Problem:**
I need a quick way to forecast the Personal Consumption Expenditures (PCE) Index for the "video, audio, photographic, and information processing equipment and media" sector (represented by BEA Series `DREQRG`) based on the effects of brent crude.

**The Value Proposition:**
We create a "Hybrid System" to bridge the gap between narrative economics and hardcore data science. We allow decision-makers to test distinct macro narratives (e.g., "What happens to tech spending if the Middle East conflict pushes oil to $120?") and receive a mathematically grounded, structural forecast of the resulting consumer behavior. 

## 3. How are we doing this? (Framework & Implementation Plan)
The implementation follows a strict four-phase architecture, combining Large Language Model (LLM) qualitative synthesis with Google Research's TimesFM quantitative engine (https://github.com/google-research/timesfm).

### Phase 1: Data Acquisition & Alignment (The Foundation)
**Goal:** Create a clean, aligned historical dataset of the target and the covariate.
*   **Target Data Extraction:** Parse `Section2All_xls - U20304-M.csv` to isolate Line 13 (Series Code: `DREQRG` - "Recreational goods and vehicles"). Transpose the monthly columns (1959M01 onward) into a standard time-series row format.
*   **Covariate Data Acquisition:** Pull historical monthly Brent Crude prices from a macroeconomic database (e.g., FRED) matching the exact date range of the `DREQRG` data up to April 2026.
*   **Data Merging:** Combine these streams into a single structural DataFrame featuring `Date`, `PCE_Index`, and `Brent_Crude`.

### Phase 2: The Qualitative Engine (Contextual Scenario Generation)
**Goal:** Translate "current events" (as of May 2026) into numerical 12-month forward trajectories for the covariate (Brent Crude) by anchoring current realities to specific historical macro regimes.

**Historical Memory Integration (The "Why"):** Equip the LLM prompt with qualitative context from key historical periods. This ensures the model understands the structural differences in past oil spikes to determine the correct elasticity regime:
*   **2007–2008 (The Demand Shock):** Brent crude peaked above $140/bbl due to a booming global economy, followed by the Great Financial Crisis. Tech spending was high until the credit freeze caused sudden, massive demand destruction.
*   **2010–2011 (Arab Spring & Tech Scarcity):** Brent crude spiked past $120/bbl due to Middle East instability. Simultaneously, the Tohoku earthquake severely crippled global semiconductor and photographic supply chains. Sector price increases were driven by severe product scarcity, not just energy costs.
*   **2021–2022 (Post-Pandemic & Ukraine War):** Oil spiked amid the Russia-Ukraine conflict and global reopening. High energy costs acted as a multiplier on already paralyzed shipping logistics and chip shortages, creating a strong positive correlation between oil prices and tech sector inflation.

**Current Macro Assessment (Analog Matching):** Evaluate the current geopolitical landscape (as of May 2026), including ongoing conflicts, OPEC+ production quotas, and global supply chain friction. Prompt the LLM to map today's reality to the closest historical analog (Demand Shock vs. Supply Shock).

**Trajectory Modeling:** Generate three distinct, monthly numerical arrays for Brent Crude representing May 2026 – May 2027, calibrated by the selected historical analog:
*   **Base Case:** The highest probability path based on current consensus and the mapped historical elasticity.
*   **Bull Case (High Oil):** A severe shock scenario (e.g., rapid conflict escalation heavily disrupting supply).
*   **Bear Case (Low Oil):** A demand-destruction scenario (e.g., global economic slowdown or unexpected supply glut).

### Phase 3: The Quantitative Engine (TimesFM Integration)
**Goal:** Process the historical data and future scenarios through the deep learning model.
*   **Model Initialization:** Load the `google-research/timesfm` library (specifically `timesfm-1.0-200m` or latest available). Configure the model with a 120-month `context_len` (10-year lookback) and a 12-month `horizon_len`.
*   **Dynamic Covariate Mapping:** Construct the specific payload required by TimesFM's `forecast_on_df` function. This involves passing the merged historical DataFrame alongside the future 12-month Brent Crude arrays from Phase 2.
*   **Execution:** Run the TimesFM inference three separate times—once for each oil scenario (Base, Bull, Bear). 

### Phase 4: Output, Analysis & Visualization
**Goal:** Deliver actionable intelligence.
*   **Data Assembly:** Aggregate the three output forecasts from TimesFM into a comparative dataset.
*   **Visualization:** Construct a unified dashboard or chart. The chart will display the historical `DREQRG` PCE index up to April 2026, branching out into a "fan of uncertainty" containing three divergent forecast lines (May 2026 to May 2027), each clearly labeled with its respective geopolitical oil scenario.

## 4. Technical Stack & Environment (The Prerequisites)
*   **Language & Runtime:** Python 3.10+.
*   **Hardware/Backend:** CPU (unless GPU/TPU is explicitly configured; ensure the correct JAX installation commands are used for the target hardware).
*   **Core Libraries:** `pandas`, `numpy`, `matplotlib`/`plotly`, `fredapi` (for Brent Crude), and `timesfm`. 
*   **Secret Management:** API keys (FRED API, OpenAI/Anthropic API for Phase 2) MUST be loaded securely via a `.env` file using `python-dotenv`. Do not hardcode keys.

## 5. Strict Constraints & Edge Cases
To ensure pipeline stability, the following rules must be enforced in the code:

**Data Alignment:**
*   **Date Anchoring:** Standardize the index to End-of-Month (e.g., `YYYY-MM-31`) across both datasets. FRED and BEA often default to different formats.
*   **Publication Lags:** Because we are operating as of May 2026, April 2026 economic data may not be fully published. If April 2026 data is missing for either target or covariate, the script must forward-fill (`ffill`) the missing value using March 2026 data to maintain alignment.
*   **Covariate Normalization:** Ensure the covariate (Brent Crude) and the target (PCE Index) are formatted correctly for TimesFM's `forecast_on_df` dynamic covariate parameters.

**LLM Operationalization:**
*   **Structured Output:** The LLM call in Phase 2 MUST use strict JSON mode or tool-calling (e.g., using `Pydantic`). The script requires the LLM to return a JSON object containing exactly three arrays (`base_case`, `bull_case`, `bear_case`), each containing 12 floats. 
*   **Fallback Logic:** If the LLM fails to return a valid JSON or times out, the script must catch the exception and default to a hardcoded fallback array (e.g., a flat line carrying the latest known oil price forward for 12 months) so the TimesFM engine can still execute.