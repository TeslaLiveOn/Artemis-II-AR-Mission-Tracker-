"""Unit tests for mission_time.timestamp_utils."""

import pytest
from datetime import datetime, timezone

from mission_time.timestamp_utils import add_time_delta, TIMEZONES


class TestAddTimeDeltaBasic:
    def test_zero_delta_returns_base_time(self):
        base = datetime(2025, 11, 16, 6, 14, tzinfo=timezone.utc)
        result = add_time_delta(base, output_tz="UTC")
        assert result["iso8601"] == "2025-11-16T06:14:00+00:00"
        assert result["unix"] == base.timestamp()
        assert result["timezone"] == "UTC"

    def test_add_hours(self):
        base = datetime(2025, 11, 16, 6, 14, tzinfo=timezone.utc)
        result = add_time_delta(base, hours=1, output_tz="UTC")
        assert result["iso8601"] == "2025-11-16T07:14:00+00:00"

    def test_add_days(self):
        base = datetime(2025, 11, 16, 6, 14, tzinfo=timezone.utc)
        result = add_time_delta(base, days=1, output_tz="UTC")
        assert result["iso8601"] == "2025-11-17T06:14:00+00:00"

    def test_add_minutes(self):
        base = datetime(2025, 11, 16, 6, 14, tzinfo=timezone.utc)
        result = add_time_delta(base, minutes=46, output_tz="UTC")
        assert result["iso8601"] == "2025-11-16T07:00:00+00:00"

    def test_add_combined_delta(self):
        # 7 hours + 645 minutes = 7h + 10h45m = 17h45m
        base = datetime(2025, 11, 16, 11, 30, tzinfo=timezone.utc)
        result = add_time_delta(base, hours=7, minutes=645, output_tz="UTC")
        assert result["iso8601"] == "2025-11-17T05:15:00+00:00"
        assert result["unix"] == 1763356500.0

    def test_negative_delta(self):
        base = datetime(2025, 11, 16, 11, 30, tzinfo=timezone.utc)
        result = add_time_delta(base, hours=-2, output_tz="UTC")
        assert result["iso8601"] == "2025-11-16T09:30:00+00:00"
        assert result["unix"] == 1763285400.0


class TestAddTimeDeltaTimezones:
    def test_et_timezone(self):
        base = datetime(2025, 11, 16, 6, 14, tzinfo=timezone.utc)
        result = add_time_delta(base, output_tz="ET")
        assert result["timezone"] == "ET"
        # November is EST (UTC-5)
        assert "-05:00" in result["iso8601"]

    def test_edt_alias(self):
        # July is EDT (UTC-4)
        base = datetime(2025, 7, 4, 12, 0, tzinfo=timezone.utc)
        result = add_time_delta(base, output_tz="EDT")
        assert result["timezone"] == "EDT"
        assert "-04:00" in result["iso8601"]

    def test_est_alias(self):
        # November is EST (UTC-5)
        base = datetime(2025, 11, 16, 6, 14, tzinfo=timezone.utc)
        result = add_time_delta(base, output_tz="EST")
        assert result["timezone"] == "EST"
        assert "-05:00" in result["iso8601"]

    def test_edt_example_from_docstring(self):
        base = datetime(2025, 11, 16, 11, 30, tzinfo=timezone.utc)
        result = add_time_delta(base, minutes=645, hours=7, output_tz="EDT")
        assert result == {
            "iso8601": "2025-11-17T00:15:00-05:00",
            "unix": 1763356500.0,
            "timezone": "EDT",
        }

    def test_invalid_timezone_raises_value_error(self):
        base = datetime(2025, 11, 16, 6, 14, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="Unknown timezone"):
            add_time_delta(base, output_tz="INVALID")

    def test_invalid_timezone_error_lists_valid_options(self):
        base = datetime(2025, 11, 16, 6, 14, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="EDT"):
            add_time_delta(base, output_tz="INVALID")


class TestAddTimeDeltaNaiveDatetime:
    def test_naive_datetime_treated_as_utc(self):
        naive = datetime(2025, 11, 16, 6, 14)  # no tzinfo
        aware = datetime(2025, 11, 16, 6, 14, tzinfo=timezone.utc)
        result_naive = add_time_delta(naive, hours=1, output_tz="UTC")
        result_aware = add_time_delta(aware, hours=1, output_tz="UTC")
        assert result_naive["iso8601"] == result_aware["iso8601"]
        assert result_naive["unix"] == result_aware["unix"]


class TestTimestampResultFields:
    def test_result_contains_iso8601(self):
        base = datetime(2025, 11, 16, 6, 14, tzinfo=timezone.utc)
        result = add_time_delta(base, output_tz="UTC")
        assert "iso8601" in result

    def test_result_contains_unix(self):
        base = datetime(2025, 11, 16, 6, 14, tzinfo=timezone.utc)
        result = add_time_delta(base, output_tz="UTC")
        assert "unix" in result
        assert isinstance(result["unix"], float)

    def test_result_contains_timezone(self):
        base = datetime(2025, 11, 16, 6, 14, tzinfo=timezone.utc)
        result = add_time_delta(base, output_tz="UTC")
        assert "timezone" in result
        assert result["timezone"] == "UTC"


class TestTimezonesRegistry:
    def test_contains_utc(self):
        assert "UTC" in TIMEZONES

    def test_contains_et(self):
        assert "ET" in TIMEZONES

    def test_contains_edt(self):
        assert "EDT" in TIMEZONES

    def test_contains_est(self):
        assert "EST" in TIMEZONES
