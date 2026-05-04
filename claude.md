1. What are we trying to accomplish? (Objective & Scope)
Objective:
To architect and deploy a 12-month hybrid forecasting pipeline that predicts the Personal Consumption Expenditures (PCE) Index for the "video, audio, photographic, and information processing equipment and media" sector (represented by BEA Series DREQRG).

Target Audience:
The end-users are business analysts who oversee overall macroeconomic trends. They are domain-literate in economics but are not deep learning engineers. The final tools and outputs (specifically the Phase 4 dashboard) must be intuitive, narrative-driven, and clearly link macroeconomic scenarios to the forecast data without hiding behind black-box machine learning jargon.

Scope:
The system will generate forecasts from May 2026 through May 2027. Instead of relying solely on historical pattern recognition, the forecast will actively incorporate forward-looking supply chain, shipping, and geopolitical logistics realities by using a proxy for supply chain friction, such as the NY Fed's Global Supply Chain Pressure Index (GSCPI) or a global freight index.

Non-Goals:

We are not building a causal inference model to explain why supply chains froze in 2021.

We are not attempting to build an algorithmic trading bot for freight futures.

Expected Deliverables:

A single chart that displays the historical PCE index (DREQRG) and the forecast for the next 12 months.

The chart should also display the historical Supply Chain/Freight index and the forecast for the next 12 months across three distinct scenarios (Base, Bull, Bear).

2. Why are we doing it? (Problem & Value Proposition)
The Problem:
I need a quick way to forecast the PCE Index for the tech and media equipment sector (DREQRG) based on the effects of global supply chain bottlenecks, semiconductor lead times, and freight costs, which directly dictate the pricing of these deflationary consumer goods.

The Value Proposition:
We create a "Hybrid System" to bridge the gap between narrative economics and hardcore data science. We allow decision-makers to test distinct macro narratives (e.g., "What happens to consumer tech spending if a blockade in the South China Sea sends shipping costs spiking 400%?") and receive a mathematically grounded, structural forecast of the resulting consumer behavior.

3. How are we doing this? (Framework & Implementation Plan)
The implementation follows a strict four-phase architecture, combining Large Language Model (LLM) qualitative synthesis with Google Research's TimesFM quantitative engine.

Phase 1: Data Acquisition & Alignment (The Foundation)
Goal: Create a clean, aligned historical dataset of the target and the covariate.

Target Data Extraction: Parse Section2All_xls - U20304-M.csv to isolate Line 13 (Series Code: DREQRG). Transpose the monthly columns into a standard time-series row format.

Covariate Data Acquisition: Pull historical monthly data for the Global Supply Chain Pressure Index (GSCPI) or a designated FRED freight/logistics series (e.g., PCU484121484121 for general freight) matching the exact date range of the DREQRG data up to April 2026.

Data Merging: Combine these streams into a single structural DataFrame featuring Date, PCE_Index, and Supply_Chain_Index.

Phase 2: The Qualitative Engine (Contextual Scenario Generation)
Goal: Translate "current events" (as of May 2026) into numerical 12-month forward trajectories for the covariate (Supply Chain / Global Freight Pressures) by anchoring current realities to specific historical macro regimes.

Historical Memory Integration (The "Why"): Equip the LLM prompt with qualitative context from key historical shock periods to determine the correct elasticity and volatility regime for global logistics. The LLM will use this context to generate the future covariate arrays:

1973–1974 (First OPEC Embargo):

Logistics Impact: Massive, unprecedented spike in shipping bunker fuel costs. Forced immediate structural changes to global shipping speeds ("slow steaming" introduced to save fuel).

Elasticity Pattern: Sudden, permanent step-up in baseline freight costs followed by severe consumer demand destruction for early consumer electronics.

1979–Early 1980s (Iranian Revolution & Volcker Shock):

Logistics Impact: A second massive logistics cost shock, quickly followed by extreme central bank interest rate hikes. The resulting stagflation heavily suppressed global trade volumes.

Elasticity Pattern: High volatility in freight rates that eventually collapsed as global trade froze under double-digit interest rates.

1990–1991 (Gulf War):

Logistics Impact: A brief panic regarding Middle Eastern shipping lanes and fuel costs.

Elasticity Pattern: A short, sharp, acute spike in supply chain friction that resolved rapidly (within months) once the conflict concluded decisively, returning quickly to baseline.

2007–2008 (Pre-GFC Boom to Global Trade Freeze):

Logistics Impact: Global shipping capacity was maxed out by a booming global economy, driving freight rates to peaks. When the financial crisis hit, trade finance (letters of credit) froze overnight, physically halting ships at ports.

Elasticity Pattern: A massive parabolic peak in shipping friction, followed by an absolute collapse to historic lows as demand vanished.

2010–2011 (Arab Spring & Physical Tech Disruptions):

Logistics Impact: Elevated shipping fuel costs met with severe, localized physical destruction of tech supply chains (the Tohoku earthquake hitting Japanese semiconductors, and Thai floods decimating global hard drive manufacturing).

Elasticity Pattern: Immediate, localized product scarcity establishing a strong price floor for electronics, with a slow decay as factories took years to rebuild.

2021–2022 (Post-Pandemic Logistics Crisis):

Logistics Impact: The ultimate supply chain freeze. Global reopening crashed into paralyzed port logistics, container deficits, and chronic semiconductor shortages.

Elasticity Pattern: A massive, sustained plateau of maximum supply chain pressure, temporarily breaking the consumer tech sector's 20-year deflationary trend due to sheer product unavailability.

Current Macro Assessment (Analog Matching): Evaluate the current geopolitical landscape (as of May 2026). Prompt the LLM to map today's reality to the closest historical analog from the list above. (e.g., "Does May 2026 look like the brief panic of 1990, or the structural freeze of 2021?")

Trajectory Modeling: Generate three distinct, monthly numerical arrays for the Supply Chain Index representing May 2026 – May 2027, calibrated by the selected historical analog:

Base Case: The highest probability path based on current consensus shipping rates and factory output.

Bull Case (High Disruption): A severe shock scenario (e.g., massive logistics bottleneck or semiconductor embargo mirroring 2021 or 1973).

Bear Case (Low Disruption): A deflationary/easing scenario (e.g., massive overcapacity in shipping networks mirroring 2008-2009).

Output Requirements:
The script requires the LLM to return a strict JSON object containing exactly three arrays (base_case, bull_case, bear_case), each containing 13 floats (May 2026 to May 2027 inclusive), plus a brief narrative string justifying which historical period was selected as the primary analog.

Phase 3: The Quantitative Engine (TimesFM Integration)
Goal: Process the historical data and future scenarios through the deep learning model.

Model Initialization: Load the google-research/timesfm library. Configure the model with a 120-month context_len (10-year lookback) and a 12-month horizon_len.

Dynamic Covariate Mapping: Construct the specific payload required by TimesFM's forecast_on_df (or forecast_with_covariates) function. This involves passing the merged historical DataFrame alongside the future 12-month Supply Chain Index arrays from Phase 2.

Execution: Run the TimesFM inference three separate times—once for each logistics scenario (Base, Bull, Bear).

Phase 4: Output, Analysis & Visualization
Goal: Deliver actionable intelligence.

Data Assembly: Aggregate the three output forecasts from TimesFM into a comparative dataset.

Visualization: Construct a unified dashboard or chart. The top panel will display the Supply Chain scenario inputs. The bottom panel will display the historical DREQRG PCE index up to April 2026, branching out into a "fan of uncertainty" containing three divergent forecast lines (May 2026 to May 2027), each clearly labeled with its respective geopolitical/logistics scenario.

4. Technical Stack & Environment (The Prerequisites)
Language & Runtime: Python 3.10+.

Hardware/Backend: CPU (unless GPU/TPU is explicitly configured).

Core Libraries: pandas, numpy, matplotlib/plotly, fredapi (or direct CSV ingestion for NY Fed GSCPI), and timesfm.

Secret Management: API keys MUST be loaded securely via a .env file using python-dotenv. Do not hardcode keys.

5. Strict Constraints
To ensure pipeline stability, the following rules must be enforced in the code:

Data Alignment:

Date Anchoring: Standardize the index to End-of-Month (e.g., YYYY-MM-31) across both datasets.

Publication Lags: Because we are operating as of May 2026, April 2026 economic data may not be fully published. If April 2026 data is missing for either target or covariate, the script must forward-fill (ffill) the missing value using March 2026 data to maintain alignment.

Covariate Normalization: Ensure the covariate (Supply Chain Index) and the target (PCE Index) are formatted correctly for TimesFM's dynamic covariate parameters, scaling inputs if the absolute values of the index drastically differ from DREQRG.

LLM Operationalization:

Structured Output: The LLM call in Phase 2 MUST use strict JSON mode or tool-calling. The script requires the LLM to return a JSON object containing exactly three arrays (base_case, bull_case, bear_case), each containing 13 floats (May 2026 to May 2027 inclusive), plus the narrative string.

Fallback Logic: If the LLM fails to return a valid JSON or times out, the script must catch the exception and default to a hardcoded fallback array (e.g., a flat line carrying the latest known index value forward) so the TimesFM engine can still execute.

6. Edge Cases

Phase 1: Data Acquisition Edge Cases
Asynchronous Publication Lags: The BEA (which publishes DREQRG) and the NY Fed (which publishes the GSCPI) do not release data on the same day.

The Risk: Your script runs in May 2026. The PCE data for April is available, but the GSCPI data for April hasn't dropped yet (or vice versa).

Mitigation: Your merging logic must be heavily fortified. Use an "as of" date parameter. If either target or covariate is missing for the anchor month, the pipeline must automatically forward-fill (ffill) the last known value, log a warning stating "Using lagged covariate," and proceed.

Negative Covariate Values:

The Risk: Unlike Brent Crude ($/bbl), the NY Fed's GSCPI is measured in standard deviations from its historical mean. It can be negative (e.g., -1.5 during periods of supply chain slack).

Mitigation: You must ensure TimesFM's normalize_xreg_target_per_input parameter handles negative dynamic covariates elegantly. (TimesFM generally handles standard scaling well, but it's vital to test this explicitly during development).

2. Phase 2: LLM Generation Edge Cases
The "Format Hallucination" (Type Error):

The Risk: The LLM returns Markdown instead of JSON, outputs an array of length 12 instead of 13, or puts a string (like "N/A") inside the float array.

Mitigation: Strict Pydantic Validation. Wrap the LLM call in a retry loop (max 2 retries). If the output fails schema validation, the pipeline catches the exception and immediately defaults to a "Naive Fallback" (e.g., carrying the latest GSCPI value forward flatly for 13 months) so Phase 3 doesn't crash.

The "Out of Bounds" Scenario:

The Risk: The LLM generates a "Bull Case" where the GSCPI spikes to +15.0 standard deviations. The historical maximum during the 2021 crisis was roughly +4.3.

Mitigation: Implement bounding logic in the prompt itself (e.g., "Do not exceed +5.0 or drop below -2.0"), or add a Python capping function post-generation to clip extreme outliers before they hit TimesFM.

3. Phase 3: TimesFM Inference Edge Cases
Out-of-Distribution (OOD) Collapse:

The Risk: Deep learning models are notoriously bad at extrapolating far beyond their training distribution. If the LLM generates a covariate spike that TimesFM has never seen in its training data, the model might output an entirely flat line or degenerate to NaN values for the DREQRG forecast.

Mitigation: Your script must include a NaN check immediately after forecast_with_covariates. If the array contains NaNs, fallback to a univariate TimesFM forecast (ignoring the covariate) for that specific scenario and log an error for the analyst.

The Deflationary Baseline Shift:

The Risk: DREQRG has been structurally deflationary for 20 years. If your Base Case GSCPI scenario is "normal" (around 0.0), TimesFM should forecast a continued downward trend in tech prices. If it forecasts an upward trend simply because the GSCPI is positive, the covariate scaling is dominating the historical trend.

Mitigation: Test the baseline early. Run a univariate forecast vs. a Base Case covariate forecast. They should look very similar.

4. Macroeconomic & Theoretical Edge Cases
The "Commodity vs. Freight" Decoupling:

The Risk: What if a massive geopolitical event occurs that only targets raw materials (e.g., an embargo on rare earth metals used in electronics) but leaves global container shipping completely untouched?

The Reality: The GSCPI would remain low, but tech prices would skyrocket. The model would forecast a drop in prices because shipping is cheap, missing the shock entirely.

Mitigation: This is an analyst-level edge case. You must clearly state on the final Phase 4 dashboard: "Note: This forecast models tech elasticity purely through the lens of global freight and supply chain bottlenecks (GSCPI)."