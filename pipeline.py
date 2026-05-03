"""
pipeline.py — testable logic for the TimesFM PCE hybrid forecasting pipeline.

Phases:
  1. Data layer   : parse_dreqrg_csv, fetch_brent_crude, merge_pce_brent
  2. Scenario     : validate_scenarios, make_forecast_dates
  3. Payload build: build_history_payload, build_future_payload
"""
from __future__ import annotations

from pathlib import Path
from typing import Union

import fredapi
import pandas as pd


# ---------------------------------------------------------------------------
# Phase 1 — Data layer
# ---------------------------------------------------------------------------

def parse_dreqrg_csv(filepath: Union[str, Path]) -> pd.DataFrame:
    """
    Parse BEA PCE price-index CSV and return the DREQRG series as a tidy
    DataFrame with columns ['Date', 'PCE_Index'].

    The CSV has 7 metadata rows before the data header, so skiprows=7.
    The two unnamed columns after 'Line' are renamed to 'Description' and
    'SeriesCode'; all remaining columns are BEA date strings (e.g. '1959M01').

    Raises
    ------
    FileNotFoundError  if *filepath* does not exist.
    ValueError         if no row with SeriesCode == 'DREQRG' is found.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    df = pd.read_csv(path, skiprows=7, header=0, low_memory=False)

    # The first three columns are: Line, Unnamed:1 (Description), Unnamed:2 (SeriesCode)
    col_map = {df.columns[1]: "Description", df.columns[2]: "SeriesCode"}
    df = df.rename(columns=col_map)

    dreqrg_rows = df[df["SeriesCode"].astype(str).str.strip() == "DREQRG"]
    if dreqrg_rows.empty:
        raise ValueError(
            "Series 'DREQRG' not found in the CSV. "
            "Check that the file is the correct BEA PCE price-index export."
        )

    row = dreqrg_rows.iloc[0]

    # Date columns are everything after the first three fixed columns
    date_cols = [c for c in df.columns if str(c).strip() not in ("Line", "Description", "SeriesCode")]

    records = []
    for col in date_cols:
        raw = str(col).strip()
        # Format: 1959M01 → 1959-01
        try:
            date = pd.to_datetime(raw.replace("M", "-"), format="%Y-%m")
        except ValueError:
            continue
        try:
            value = float(row[col])
        except (ValueError, TypeError):
            continue
        records.append({"Date": date, "PCE_Index": value})

    result = (
        pd.DataFrame(records)
        .sort_values("Date")
        .reset_index(drop=True)
    )
    result["PCE_Index"] = result["PCE_Index"].astype(float)
    return result


def fetch_brent_crude(
    api_key: str,
    start: str = "1987-01-01",
    end: str = "2026-04-30",
) -> pd.DataFrame:
    """
    Fetch monthly Brent Crude prices (DCOILBRENTEU) from FRED.

    Returns a DataFrame with columns ['Date', 'Brent_Crude'] at month-start
    frequency. Gaps of at most one month are forward-filled.

    Parameters
    ----------
    api_key : FRED API key (get a free one at fred.stlouisfed.org)
    start   : ISO date string for the start of the fetch range
    end     : ISO date string for the end of the fetch range
    """
    fred = fredapi.Fred(api_key=api_key)
    series = fred.get_series("DCOILBRENTEU", observation_start=start, observation_end=end)

    # Normalise index to month-start (floor each date to the 1st of its month)
    series.index = series.index.to_period("M").to_timestamp()

    # Resample to monthly, forward-fill at most one period for small gaps
    series = series.resample("MS").last().ffill(limit=1)

    df = series.dropna().reset_index()
    df.columns = ["Date", "Brent_Crude"]
    df["Date"] = pd.to_datetime(df["Date"])
    df["Brent_Crude"] = df["Brent_Crude"].astype(float)
    return df


def merge_pce_brent(pce_df: pd.DataFrame, brent_df: pd.DataFrame) -> pd.DataFrame:
    """
    Inner-join PCE and Brent Crude DataFrames on the 'Date' column.

    Returns a DataFrame with columns ['Date', 'PCE_Index', 'Brent_Crude']
    containing only rows present in both inputs with no NaN values.

    Raises
    ------
    ValueError  if the inner join produces an empty result (no date overlap).
    """
    merged = pd.merge(pce_df, brent_df, on="Date", how="inner")
    merged = merged.dropna(subset=["PCE_Index", "Brent_Crude"])

    if merged.empty:
        raise ValueError(
            "No overlap between PCE dates and Brent Crude dates. "
            "Verify both DataFrames share a common date range."
        )

    merged = merged[["Date", "PCE_Index", "Brent_Crude"]].reset_index(drop=True)
    merged["Date"] = pd.to_datetime(merged["Date"])
    return merged


# ---------------------------------------------------------------------------
# Phase 2 — Scenario validation
# ---------------------------------------------------------------------------

def validate_scenarios(
    base: list[float],
    bull: list[float],
    bear: list[float],
    expected_len: int = 13,
) -> None:
    """
    Validate three Brent Crude oil scenario arrays.

    Raises
    ------
    ValueError   if any list has wrong length or contains a negative price.
    TypeError    if any element is non-numeric.
    """
    for name, scenario in (("base", base), ("bull", bull), ("bear", bear)):
        if len(scenario) != expected_len:
            raise ValueError(
                f"Length mismatch: '{name}' scenario has {len(scenario)} elements, "
                f"expected {expected_len}."
            )
        for i, val in enumerate(scenario):
            if not isinstance(val, (int, float)):
                raise TypeError(
                    f"Non-numeric value in '{name}' scenario at index {i}: {val!r}"
                )
            if val < 0:
                raise ValueError(
                    f"Negative price in '{name}' scenario at index {i}: {val}"
                )


def make_forecast_dates(
    start: str = "2026-05-01",
    periods: int = 13,
) -> pd.DatetimeIndex:
    """
    Return a DatetimeIndex of month-start dates for the forecast window.

    Default: May 2026 through May 2027 (13 months, inclusive on both ends).
    """
    return pd.date_range(start=start, periods=periods, freq="MS")


# ---------------------------------------------------------------------------
# Phase 3 — TimesFM payload builders
# ---------------------------------------------------------------------------

def build_history_payload(
    merged_df: pd.DataFrame,
    context_len: int = 120,
    unique_id: str = "DREQRG",
) -> pd.DataFrame:
    """
    Build the historical input DataFrame for TimesFM.

    Returns the last *context_len* rows of *merged_df* reformatted as
    ['unique_id', 'ds', 'y', 'Brent_Crude'].

    Raises
    ------
    ValueError  if *merged_df* has fewer rows than *context_len*.
    """
    if len(merged_df) < context_len:
        raise ValueError(
            f"Insufficient history: need {context_len} rows but only "
            f"{len(merged_df)} are available."
        )

    tail = merged_df.tail(context_len).copy()
    payload = pd.DataFrame({
        "unique_id": unique_id,
        "ds": pd.to_datetime(tail["Date"].values),
        "y": tail["PCE_Index"].astype(float).values,
        "Brent_Crude": tail["Brent_Crude"].astype(float).values,
    })
    return payload.reset_index(drop=True)


def build_future_payload(
    scenario: list[float],
    forecast_dates: pd.DatetimeIndex,
    unique_id: str = "DREQRG",
) -> pd.DataFrame:
    """
    Build the future covariate DataFrame for TimesFM.

    Returns a DataFrame with columns ['unique_id', 'ds', 'Brent_Crude']
    aligned to *forecast_dates*.

    Raises
    ------
    ValueError  if len(scenario) != len(forecast_dates).
    """
    if len(scenario) != len(forecast_dates):
        raise ValueError(
            f"Length mismatch: scenario has {len(scenario)} values but "
            f"forecast_dates has {len(forecast_dates)} entries."
        )

    return pd.DataFrame({
        "unique_id": unique_id,
        "ds": pd.DatetimeIndex(forecast_dates),
        "Brent_Crude": [float(v) for v in scenario],
    })
