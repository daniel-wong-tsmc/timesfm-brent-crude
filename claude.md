1. What are we trying to accomplish? (Objective & Scope)
Objective
To architect and deploy a 12-month hybrid forecasting pipeline that predicts the Personal Consumption Expenditures (PCE) Index for the "video, audio, photographic, and information processing equipment and media" sector (represented by BEA Series DVAPRA). The overall setup and outcomes must be explainable by non-technical personnel.

Target Audience
The end-users are business analysts who oversee overall macroeconomic trends. The final tools and outputs (specifically the Phase 4 dashboard) must be intuitive, narrative-driven, and clearly link macroeconomic scenarios to the forecast data without machine learning jargon.

Scope
The system will generate forecasts from May 2026 through May 2027. Instead of relying solely on historical pattern recognition, the forecast will actively incorporate forward-looking energy costs, physical input constraints, and geopolitical risk by using Brent Crude Oil Prices (FRED Series: POILBREUSDM) as the primary dynamic covariate.

Non-Goals
We are not building a causal inference model to explain why oil crashed in 2020 or spiked in 2022.

We are not attempting to build an algorithmic trading bot for crude oil futures.

Expected Deliverables
A single chart that displays the historical PCE index (DVAPRA) and the forecast for the next 12 months.

A chart displaying the historical Brent Crude price and the forecast for the next 12 months across three distinct scenarios (Base, Bull, Bear).

2. Why are we doing it? (Problem & Value Proposition)
The Problem
I need a quick way to forecast the PCE Index for the tech and media equipment sector (DVAPRA) based on the effects of global energy markets. Brent Crude acts as a foundational benchmark for global inflation, directly dictating the cost of shipping fuel (bunker fuel), aviation cargo rates, and petroleum-derived raw materials (plastics/resins) used heavily in consumer electronics.

3. Overall Logic
We will first forecast brent crude using TimesFM and we will have 3 scenarios, bull, base, and bear. Bull case will follow the brent crude price trajectory from 2010Q3 - 2012Q4, base case will be following brent crude price trajectory from 2021Q1 - 2022Q2, and bear case will be 2007Q1 - 2009Q1. Using the forecasted brent crude, we will use this as the exogenous variable to use TimesFM again to forecast DVAPRA. 