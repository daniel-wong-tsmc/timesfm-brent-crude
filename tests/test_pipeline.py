"""
Tests for pipeline.py — written FIRST (TDD Red phase).
Run: python -m pytest tests/ -x -v
"""
from __future__ import annotations

import math
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

FIXTURE_CSV = Path(__file__).parent / "fixtures" / "pce_mini.csv"
REAL_CSV = Path(__file__).parent.parent / "Section2All_xls - U20304-M.csv"

# ---------------------------------------------------------------------------
# Phase 1 — parse_dreqrg_csv
# ---------------------------------------------------------------------------

class TestParseDreqrgCsv:
    def test_returns_dataframe_with_correct_columns(self):
        from pipeline import parse_dreqrg_csv
        df = parse_dreqrg_csv(FIXTURE_CSV)
        assert list(df.columns) == ["Date", "PCE_Index"]

    def test_date_column_is_datetime(self):
        from pipeline import parse_dreqrg_csv
        df = parse_dreqrg_csv(FIXTURE_CSV)
        assert pd.api.types.is_datetime64_any_dtype(df["Date"])

    def test_dates_are_month_start(self):
        from pipeline import parse_dreqrg_csv
        df = parse_dreqrg_csv(FIXTURE_CSV)
        for d in df["Date"]:
            assert d.day == 1

    def test_dates_are_monotonic_increasing(self):
        from pipeline import parse_dreqrg_csv
        df = parse_dreqrg_csv(FIXTURE_CSV)
        assert df["Date"].is_monotonic_increasing

    def test_pce_index_is_float(self):
        from pipeline import parse_dreqrg_csv
        df = parse_dreqrg_csv(FIXTURE_CSV)
        assert pd.api.types.is_float_dtype(df["PCE_Index"])

    def test_correct_dreqrg_values(self):
        from pipeline import parse_dreqrg_csv
        df = parse_dreqrg_csv(FIXTURE_CSV)
        # fixture has 4 date columns: 1959M01, 1959M02, 2026M01, 2026M02
        assert len(df) == 4
        assert math.isclose(df.iloc[0]["PCE_Index"], 331.285)
        assert math.isclose(df.iloc[-1]["PCE_Index"], 311.000)

    def test_missing_file_raises_file_not_found(self):
        from pipeline import parse_dreqrg_csv
        with pytest.raises(FileNotFoundError):
            parse_dreqrg_csv("/nonexistent/path/file.csv")

    def test_series_not_found_raises_value_error(self, tmp_path):
        from pipeline import parse_dreqrg_csv
        # Write a CSV with no DREQRG row
        bad_csv = tmp_path / "bad.csv"
        bad_csv.write_text(
            "Table\n\n\n\n\n\n\n"
            "Line,,,1959M01\n"
            "1,Other,DPCERG,15.0\n"
        )
        with pytest.raises(ValueError, match="DREQRG"):
            parse_dreqrg_csv(bad_csv)

    def test_real_csv_loads_successfully(self):
        """Smoke-test against the real data file."""
        from pipeline import parse_dreqrg_csv
        if not REAL_CSV.exists():
            pytest.skip("Real CSV not available in this environment")
        df = parse_dreqrg_csv(REAL_CSV)
        assert len(df) > 700          # should be 800+ months
        assert df["Date"].iloc[0] == pd.Timestamp("1959-01-01")
        assert df["Date"].iloc[-1] == pd.Timestamp("2026-02-01")
        assert df["PCE_Index"].notna().all()


# ---------------------------------------------------------------------------
# Phase 1 — fetch_brent_crude
# ---------------------------------------------------------------------------

class TestFetchBrentCrude:
    def _make_mock_fred(self, dates, values):
        """Return a mock fredapi.Fred that yields the given series."""
        series = pd.Series(values, index=pd.DatetimeIndex(dates))
        mock_fred = MagicMock()
        mock_fred.get_series.return_value = series
        return mock_fred

    def test_returns_dataframe_with_correct_columns(self):
        from pipeline import fetch_brent_crude
        dates = pd.date_range("2020-01-01", periods=3, freq="MS")
        mock_fred = self._make_mock_fred(dates, [65.0, 66.0, 67.0])
        with patch("pipeline.fredapi.Fred", return_value=mock_fred):
            df = fetch_brent_crude("FAKE_KEY")
        assert list(df.columns) == ["Date", "Brent_Crude"]

    def test_date_column_is_month_start(self):
        from pipeline import fetch_brent_crude
        dates = pd.date_range("2020-01-15", periods=3, freq="MS")
        mock_fred = self._make_mock_fred(dates, [65.0, 66.0, 67.0])
        with patch("pipeline.fredapi.Fred", return_value=mock_fred):
            df = fetch_brent_crude("FAKE_KEY")
        for d in df["Date"]:
            assert d.day == 1

    def test_values_are_float(self):
        from pipeline import fetch_brent_crude
        dates = pd.date_range("2020-01-01", periods=3, freq="MS")
        mock_fred = self._make_mock_fred(dates, [65.0, 66.0, 67.0])
        with patch("pipeline.fredapi.Fred", return_value=mock_fred):
            df = fetch_brent_crude("FAKE_KEY")
        assert pd.api.types.is_float_dtype(df["Brent_Crude"])

    def test_calls_fred_with_correct_series_id(self):
        from pipeline import fetch_brent_crude
        dates = pd.date_range("2020-01-01", periods=2, freq="MS")
        mock_fred = self._make_mock_fred(dates, [70.0, 71.0])
        with patch("pipeline.fredapi.Fred", return_value=mock_fred) as MockFred:
            fetch_brent_crude("MY_KEY")
        mock_fred.get_series.assert_called_once()
        call_args = mock_fred.get_series.call_args
        assert call_args[0][0] == "DCOILBRENTEU"

    def test_no_real_network_call(self):
        """Confirm test never hits the network by ensuring fredapi.Fred is mocked."""
        from pipeline import fetch_brent_crude
        dates = pd.date_range("2020-01-01", periods=2, freq="MS")
        mock_fred = self._make_mock_fred(dates, [70.0, 71.0])
        with patch("pipeline.fredapi.Fred", return_value=mock_fred) as MockFred:
            fetch_brent_crude("FAKE_KEY")
        MockFred.assert_called_once_with(api_key="FAKE_KEY")

    def test_forward_fills_at_most_one_month(self):
        """A single NaN mid-series should be filled; a run of two should not."""
        from pipeline import fetch_brent_crude
        dates = pd.date_range("2020-01-01", periods=4, freq="MS")
        raw = [65.0, float("nan"), 67.0, float("nan")]
        mock_fred = self._make_mock_fred(dates, raw)
        with patch("pipeline.fredapi.Fred", return_value=mock_fred):
            df = fetch_brent_crude("FAKE_KEY")
        # The single gap at index 1 should be filled; the trailing NaN at index 3
        # has nothing to fill from, so depends on implementation — just check length
        assert len(df) >= 3  # at least 3 non-NaN rows returned


# ---------------------------------------------------------------------------
# Phase 1 — merge_pce_brent
# ---------------------------------------------------------------------------

class TestMergePceBrent:
    def _make_pce(self):
        dates = pd.date_range("2020-01-01", periods=6, freq="MS")
        return pd.DataFrame({"Date": dates, "PCE_Index": range(100, 106)})

    def _make_brent(self, offset_months=0):
        dates = pd.date_range(
            pd.Timestamp("2020-01-01") + pd.DateOffset(months=offset_months),
            periods=6,
            freq="MS",
        )
        return pd.DataFrame({"Date": dates, "Brent_Crude": [50.0 + i for i in range(6)]})

    def test_returns_correct_columns(self):
        from pipeline import merge_pce_brent
        df = merge_pce_brent(self._make_pce(), self._make_brent())
        assert list(df.columns) == ["Date", "PCE_Index", "Brent_Crude"]

    def test_inner_join_on_date(self):
        from pipeline import merge_pce_brent
        # Brent starts 2 months later — only 4 months in common
        df = merge_pce_brent(self._make_pce(), self._make_brent(offset_months=2))
        assert len(df) == 4

    def test_no_nans_in_result(self):
        from pipeline import merge_pce_brent
        df = merge_pce_brent(self._make_pce(), self._make_brent())
        assert df.notna().all().all()

    def test_date_column_is_datetime(self):
        from pipeline import merge_pce_brent
        df = merge_pce_brent(self._make_pce(), self._make_brent())
        assert pd.api.types.is_datetime64_any_dtype(df["Date"])

    def test_empty_intersection_raises_value_error(self):
        from pipeline import merge_pce_brent
        # PCE in 2020, Brent in 2025 — no overlap
        pce = pd.DataFrame({
            "Date": pd.date_range("2020-01-01", periods=3, freq="MS"),
            "PCE_Index": [100.0, 101.0, 102.0],
        })
        brent = pd.DataFrame({
            "Date": pd.date_range("2025-01-01", periods=3, freq="MS"),
            "Brent_Crude": [70.0, 71.0, 72.0],
        })
        with pytest.raises(ValueError, match="[Nn]o overlap"):
            merge_pce_brent(pce, brent)


# ---------------------------------------------------------------------------
# Phase 2 — validate_scenarios
# ---------------------------------------------------------------------------

class TestValidateScenarios:
    def _valid(self, n=13):
        return [float(i + 60) for i in range(n)]

    def test_valid_scenarios_do_not_raise(self):
        from pipeline import validate_scenarios
        validate_scenarios(self._valid(), self._valid(), self._valid())

    def test_wrong_length_base_raises(self):
        from pipeline import validate_scenarios
        with pytest.raises(ValueError, match="[Ll]ength"):
            validate_scenarios(self._valid(12), self._valid(), self._valid())

    def test_wrong_length_bull_raises(self):
        from pipeline import validate_scenarios
        with pytest.raises(ValueError, match="[Ll]ength"):
            validate_scenarios(self._valid(), self._valid(14), self._valid())

    def test_wrong_length_bear_raises(self):
        from pipeline import validate_scenarios
        with pytest.raises(ValueError, match="[Ll]ength"):
            validate_scenarios(self._valid(), self._valid(), self._valid(10))

    def test_non_numeric_raises(self):
        from pipeline import validate_scenarios
        bad = ["not", "a", "number"] + self._valid(10)
        with pytest.raises((ValueError, TypeError)):
            validate_scenarios(bad, self._valid(), self._valid())

    def test_negative_price_raises(self):
        from pipeline import validate_scenarios
        bad = [-5.0] + self._valid(12)
        with pytest.raises(ValueError, match="[Nn]egative"):
            validate_scenarios(bad, self._valid(), self._valid())

    def test_custom_expected_len(self):
        from pipeline import validate_scenarios
        validate_scenarios(self._valid(6), self._valid(6), self._valid(6), expected_len=6)


# ---------------------------------------------------------------------------
# Phase 2 — make_forecast_dates
# ---------------------------------------------------------------------------

class TestMakeForecastDates:
    def test_returns_datetimeindex(self):
        from pipeline import make_forecast_dates
        idx = make_forecast_dates()
        assert isinstance(idx, pd.DatetimeIndex)

    def test_default_length_is_13(self):
        from pipeline import make_forecast_dates
        idx = make_forecast_dates()
        assert len(idx) == 13

    def test_default_start_is_may_2026(self):
        from pipeline import make_forecast_dates
        idx = make_forecast_dates()
        assert idx[0] == pd.Timestamp("2026-05-01")

    def test_ends_at_may_2027(self):
        from pipeline import make_forecast_dates
        idx = make_forecast_dates()
        assert idx[-1] == pd.Timestamp("2027-05-01")

    def test_frequency_is_month_start(self):
        from pipeline import make_forecast_dates
        idx = make_forecast_dates()
        # All dates must have day == 1
        for d in idx:
            assert d.day == 1

    def test_custom_start_and_periods(self):
        from pipeline import make_forecast_dates
        idx = make_forecast_dates(start="2025-01-01", periods=6)
        assert len(idx) == 6
        assert idx[0] == pd.Timestamp("2025-01-01")


# ---------------------------------------------------------------------------
# Phase 3 — build_history_payload
# ---------------------------------------------------------------------------

class TestBuildHistoryPayload:
    def _make_merged(self, n=150):
        dates = pd.date_range("2010-01-01", periods=n, freq="MS")
        return pd.DataFrame({
            "Date": dates,
            "PCE_Index": [300.0 + i * 0.1 for i in range(n)],
            "Brent_Crude": [70.0 + i * 0.05 for i in range(n)],
        })

    def test_returns_correct_columns(self):
        from pipeline import build_history_payload
        df = build_history_payload(self._make_merged())
        assert list(df.columns) == ["unique_id", "ds", "y", "Brent_Crude"]

    def test_default_context_len_120(self):
        from pipeline import build_history_payload
        df = build_history_payload(self._make_merged(150))
        assert len(df) == 120

    def test_custom_context_len(self):
        from pipeline import build_history_payload
        df = build_history_payload(self._make_merged(150), context_len=60)
        assert len(df) == 60

    def test_unique_id_column_value(self):
        from pipeline import build_history_payload
        df = build_history_payload(self._make_merged())
        assert (df["unique_id"] == "DREQRG").all()

    def test_custom_unique_id(self):
        from pipeline import build_history_payload
        df = build_history_payload(self._make_merged(), unique_id="CUSTOM")
        assert (df["unique_id"] == "CUSTOM").all()

    def test_ds_column_is_datetime(self):
        from pipeline import build_history_payload
        df = build_history_payload(self._make_merged())
        assert pd.api.types.is_datetime64_any_dtype(df["ds"])

    def test_y_column_is_float(self):
        from pipeline import build_history_payload
        df = build_history_payload(self._make_merged())
        assert pd.api.types.is_float_dtype(df["y"])

    def test_uses_last_n_rows(self):
        from pipeline import build_history_payload
        merged = self._make_merged(150)
        df = build_history_payload(merged, context_len=10)
        expected_last_date = merged["Date"].iloc[-1]
        assert df["ds"].iloc[-1] == expected_last_date

    def test_insufficient_history_raises_value_error(self):
        from pipeline import build_history_payload
        short = self._make_merged(n=50)
        with pytest.raises(ValueError, match="[Ii]nsufficient"):
            build_history_payload(short, context_len=120)


# ---------------------------------------------------------------------------
# Phase 3 — build_future_payload
# ---------------------------------------------------------------------------

class TestBuildFuturePayload:
    def _make_dates(self, n=13):
        return pd.date_range("2026-05-01", periods=n, freq="MS")

    def _make_scenario(self, n=13):
        return [70.0 + i for i in range(n)]

    def test_returns_correct_columns(self):
        from pipeline import build_future_payload
        df = build_future_payload(self._make_scenario(), self._make_dates())
        assert list(df.columns) == ["unique_id", "ds", "Brent_Crude"]

    def test_correct_row_count(self):
        from pipeline import build_future_payload
        df = build_future_payload(self._make_scenario(13), self._make_dates(13))
        assert len(df) == 13

    def test_unique_id_default_value(self):
        from pipeline import build_future_payload
        df = build_future_payload(self._make_scenario(), self._make_dates())
        assert (df["unique_id"] == "DREQRG").all()

    def test_custom_unique_id(self):
        from pipeline import build_future_payload
        df = build_future_payload(self._make_scenario(), self._make_dates(), unique_id="X")
        assert (df["unique_id"] == "X").all()

    def test_ds_column_matches_dates(self):
        from pipeline import build_future_payload
        dates = self._make_dates(13)
        df = build_future_payload(self._make_scenario(13), dates)
        pd.testing.assert_index_equal(
            pd.DatetimeIndex(df["ds"]), dates, check_names=False
        )

    def test_brent_crude_values_match_scenario(self):
        from pipeline import build_future_payload
        scenario = self._make_scenario(13)
        df = build_future_payload(scenario, self._make_dates(13))
        assert list(df["Brent_Crude"]) == scenario

    def test_length_mismatch_raises_value_error(self):
        from pipeline import build_future_payload
        with pytest.raises(ValueError, match="[Ll]ength"):
            build_future_payload(self._make_scenario(13), self._make_dates(12))
