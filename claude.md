1. What are we trying to accomplish? (Objective & Scope)
Objective
To architect and deploy a 12-month hybrid forecasting pipeline that predicts the Personal Consumption Expenditures (PCE) Index for the "video, audio, photographic, and information processing equipment and media" sector (represented by BEA Series DREQRG).

Target Audience
The end-users are business analysts who oversee overall macroeconomic trends. The final tools and outputs (specifically the Phase 4 dashboard) must be intuitive, narrative-driven, and clearly link macroeconomic scenarios to the forecast data without machine learning jargon.

Scope
The system will generate forecasts from May 2026 through May 2027. Instead of relying solely on historical pattern recognition, the forecast will actively incorporate forward-looking energy costs, physical input constraints, and geopolitical risk by using Brent Crude Oil Prices (FRED Series: POILBREUSDM) as the primary dynamic covariate.

Non-Goals
We are not building a causal inference model to explain why oil crashed in 2020 or spiked in 2022.

We are not attempting to build an algorithmic trading bot for crude oil futures.

Expected Deliverables
A single chart that displays the historical PCE index (DREQRG) and the forecast for the next 12 months.

A chart displaying the historical Brent Crude price and the forecast for the next 12 months across three distinct scenarios (Base, Bull, Bear).

2. Why are we doing it? (Problem & Value Proposition)
The Problem
I need a quick way to forecast the PCE Index for the tech and media equipment sector (DREQRG) based on the effects of global energy markets. Brent Crude acts as a foundational benchmark for global inflation, directly dictating the cost of shipping fuel (bunker fuel), aviation cargo rates, and petroleum-derived raw materials (plastics/resins) used heavily in consumer electronics.

The Value Proposition
We create a "Hybrid System" to bridge the gap between narrative economics and hardcore data science. We allow decision-makers to test distinct macro narratives (e.g., "What happens to consumer tech spending if an escalation in the Middle East sends Brent to $150/bbl?") and receive a mathematically grounded, structural forecast of the resulting consumer behavior.

3. How are we doing this? (Framework & Implementation Plan)
The implementation follows a strict four-phase architecture, combining Large Language Model (LLM) qualitative synthesis with Google Research's TimesFM quantitative engine.

Phase 1: Data Acquisition & Alignment (The Foundation)
Goal: Create a clean, aligned historical dataset of the target and the covariate.

Target Data Extraction: Parse Section2All_xls - U20304-M.csv to isolate Line 13 (Series Code: DREQRG). Transpose the monthly columns into a standard time-series row format.

Covariate Data Acquisition (API Integration): Use the fredapi library to authenticate and dynamically pull the global price of Brent Crude (POILBREUSDM), ensuring the date range matches the DREQRG data up to April 2026.

Data Merging: Combine these streams into a single structural DataFrame featuring Date, PCE_Index, and Brent_Crude_Price.

Phase 2: The Qualitative Engine (Contextual Scenario Generation)
Goal: Translate "current events" (as of May 2026) into numerical 12-month forward trajectories for Brent Crude by anchoring current realities to specific historical macro regimes.

Historical Memory Integration (The "Why"): Equip the LLM prompt with qualitative context from key historical oil shock periods to determine the correct elasticity and volatility regime:

* 1973–1974 (First OPEC Embargo): The archetype for structural supply shocks. Oil prices quadrupled, embedding permanent inflation into supply chains and destroying consumer discretionary demand.
* 1979–1980 (Iranian Revolution & Volcker Shock): The Second Oil Shock. Severe supply disruption doubled prices, accelerating stagflation. This forced double-digit interest rates, ultimately crashing global economic demand and bringing prices back down.
* 1990–1991 (Gulf War): A brief panic regarding Middle Eastern supply. A short, sharp, acute spike in oil prices that resolved rapidly within months once the conflict concluded, returning quickly to baseline.
* 2007–2008 (Commodity Supercycle): Unprecedented global demand pushed oil to a record $147/bbl, followed by an absolute collapse to $40/bbl as the financial crisis destroyed global demand.
* 2010–2011 (Arab Spring): Geopolitical instability across the MENA region. Oil spiked back over $100/bbl post-GFC, establishing a multi-year, sustained high-price plateau ($100-$110 range) that acted as a heavy tax on consumer spending.
* 2021–2022 (The Reopening Squeeze & Geopolitical Shock): A compound crisis. First, a rapid post-pandemic economic reopening caused demand to outpace severely constrained supply. Then, the Russia-Ukraine conflict sparked a massive geopolitical supply panic. This combination sent Brent climbing steadily from $50 to a massive spike over $130/bbl, embedding heavy friction into global logistics.

Current Macro Assessment (Analog Matching): Evaluate the geopolitical landscape as of May 2026. Prompt the LLM to map today's reality to the closest historical analog above.

Trajectory Modeling: Generate three distinct, monthly numerical arrays for Brent Crude (in USD per barrel) representing May 2026 – May 2027:

Base Case: Highest probability path based on current futures curves and OPEC+ production consensus.

Bull Case (High Disruption): A severe supply shock scenario (e.g., $150+/bbl mirroring 1973 or 2022). (Note: "Bull" here implies high oil prices, which is generally bearish for the broader economy).

Bear Case (Low Disruption/Deflation): A deflationary demand destruction scenario (e.g., prices dropping below $50/bbl mirroring 2008 or 2020).

Output Requirements: The script requires the LLM to return a strict JSON object containing exactly three arrays (base_case, bull_case, bear_case), each containing 13 floats (May 2026 to May 2027 inclusive), plus a brief narrative string justifying the selected historical analog.

Phase 3: The Quantitative Engine (TimesFM Integration)
Goal: Process the historical data and future scenarios through the deep learning model.

Model Initialization: Load the google-research/timesfm library (specifically targeting the 2.5 PyTorch architecture with xreg support). Configure the model with a 120-month context_len (10-year lookback) and a 12-month horizon_len.

Dynamic Covariate Mapping: Construct the specific payload required by TimesFM, passing the merged historical DataFrame alongside the future 12-month Brent Crude arrays from Phase 2.

Execution: Run the TimesFM inference three separate times—once for each energy scenario (Base, Bull, Bear).

Phase 4: Output, Analysis & Visualization
Goal: Deliver actionable intelligence.

Data Assembly: Aggregate the three output forecasts from TimesFM into a comparative dataset.

Visualization: Construct a unified dashboard. The top panel will display the Brent Crude scenario inputs (in USD). The bottom panel will display the historical DREQRG PCE index branching out into a "fan of uncertainty" containing three divergent forecast lines, each labeled with its respective macro energy scenario.

4. Technical Stack & Environment (The Prerequisites)
Language & Runtime: Python 3.10+.

Hardware/Backend: CPU (unless GPU/TPU is explicitly configured).

Core Libraries: pandas, numpy, plotly, fredapi, and timesfm[torch,xreg].

Secret Management: FRED API keys and LLM API keys MUST be loaded securely via a .env file using python-dotenv. Do not hardcode keys.

5. Strict Constraints
Data Alignment & API Handling
FRED API Execution: The pipeline must securely pass the FRED API key from the environment variables to the fredapi.Fred() client.

Date Anchoring: Standardize the index to End-of-Month (e.g., YYYY-MM-31) across both datasets. POILBREUSDM is published monthly, but timestamps must be explicitly unified with the BEA data.

Publication Lags: If April 2026 data is missing for either target or covariate, the script must forward-fill (ffill) the missing value using March 2026 data to maintain alignment.

LLM Operationalization
Structured Output: The LLM call MUST use strict JSON mode or tool-calling. It must return a JSON object with exactly three 13-float arrays and a narrative string.

Fallback Logic: If the LLM fails to return valid JSON, the script must catch the exception and default to a flat line carrying the latest known Brent Crude price forward.

6. Edge Cases
Phase 1: Data Acquisition Edge Cases
API Rate Limits or Downtime:

The Risk: The FRED API is unreachable, times out, or the API key is invalid/rate-limited.

Mitigation: Wrap the fredapi call in a try/except block. If the API fails, the pipeline must attempt to load a locally cached brent_crude_backup.csv to prevent a total pipeline failure.

Asynchronous Publication Lags:

The Risk: PCE data for April is available, but FRED hasn't published April's Brent Crude average yet.

Mitigation: Automatically forward-fill (ffill) missing anchor month values and log a warning ("Using lagged covariate for Brent Crude").

Phase 2: LLM Generation Edge Cases
The "Out of Bounds" Scenario:

The Risk: The LLM generates a mathematically absurd price (e.g., Brent dropping to -$50 or spiking to $1,000/bbl).

Mitigation: Implement bounding logic in the prompt (e.g., "$20 to $250/bbl") and add a Python capping function post-generation np.clip(array, 20, 250) to clip extreme outliers before they hit TimesFM.

The "Format Hallucination":

Mitigation: Strict Pydantic Validation. Wrap the LLM call in a retry loop (max 2 retries). If it fails, default to a "Naive Fallback."

Phase 3: TimesFM Inference Edge Cases
Out-of-Distribution (OOD) Collapse:

The Risk: The model outputs a flat line or NaNs if given an oil spike it has never seen in training (e.g., moving rapidly from $80 to $250).

Mitigation: Include a NaN check after forecasting. If NaNs are present, fallback to a univariate TimesFM forecast and log an error.

The Deflationary Baseline Shift:

The Risk: DREQRG is structurally deflationary. If high oil prices historically correlate with overall tech price drops (due to demand destruction), the model might forecast severe tech deflation during an oil spike.

Mitigation: The analyst must interpret the output carefully. Run a univariate forecast vs. a Base Case covariate forecast early on to establish the model's structural baseline behavior.

Macroeconomic & Theoretical Edge Cases
The "Energy vs. Tech" Decoupling:

The Risk: A tech-specific shock occurs (like a massive AI server boom or a semiconductor embargo) that skyrockets tech prices while global oil remains cheap.

The Reality: The model will miss this completely because it is only looking at petroleum energy costs.

Mitigation: Clearly state on the final dashboard: "Note: This forecast models tech elasticity purely through the lens of global energy input costs and logistics (Brent Crude)."