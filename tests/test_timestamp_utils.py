"""
test_timestamp_utils.py
=======================
Comprehensive unit tests for :mod:`mission_time.timestamp_utils` and
:mod:`mission_time.mission_timeline`.
"""

import math
import unittest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from mission_time.timestamp_utils import add_time_delta, TIMEZONES, TimestampResult
from mission_time.mission_timeline import (
    MISSION_EVENTS,
    project_timeline,
    print_timeline,
)

UTC = timezone.utc
ET = ZoneInfo("America/New_York")

# A fixed UTC reference point used throughout the tests:
# 2025-11-16T11:30:00Z  (mid-morning UTC, to keep ET offsets predictable)
BASE_UTC = datetime(2025, 11, 16, 11, 30, 0, tzinfo=UTC)


class TestReturnType(unittest.TestCase):
    """add_time_delta always returns a well-formed TimestampResult."""

    def test_keys_present(self):
        result = add_time_delta(BASE_UTC)
        self.assertIn("iso8601", result)
        self.assertIn("unix", result)
        self.assertIn("timezone", result)

    def test_iso8601_is_string(self):
        result = add_time_delta(BASE_UTC)
        self.assertIsInstance(result["iso8601"], str)

    def test_unix_is_float(self):
        result = add_time_delta(BASE_UTC)
        self.assertIsInstance(result["unix"], float)

    def test_timezone_field_matches_argument(self):
        for tz in TIMEZONES:
            with self.subTest(tz=tz):
                result = add_time_delta(BASE_UTC, output_tz=tz)
                self.assertEqual(result["timezone"], tz)


class TestNaiveInputAssumedUTC(unittest.TestCase):
    """Naive datetimes must be treated as UTC."""

    def test_naive_equals_utc_aware(self):
        naive = datetime(2025, 11, 16, 11, 30, 0)  # no tzinfo
        aware = BASE_UTC
        r_naive = add_time_delta(naive, hours=3)
        r_aware = add_time_delta(aware, hours=3)
        self.assertEqual(r_naive["unix"], r_aware["unix"])
        self.assertEqual(r_naive["iso8601"], r_aware["iso8601"])


class TestZeroDelta(unittest.TestCase):
    """With zero delta the output timestamp equals the input."""

    def test_zero_delta_utc(self):
        result = add_time_delta(BASE_UTC, output_tz="UTC")
        self.assertEqual(result["iso8601"], "2025-11-16T11:30:00+00:00")
        self.assertEqual(result["unix"], BASE_UTC.timestamp())

    def test_zero_delta_et(self):
        # November → EST = UTC-5, so 11:30 UTC → 06:30 EST
        result = add_time_delta(BASE_UTC, output_tz="ET")
        self.assertIn("-05:00", result["iso8601"])
        self.assertTrue(result["iso8601"].startswith("2025-11-16T06:30:00"))


class TestMinutesAddition(unittest.TestCase):
    """Minute-level arithmetic is exact."""

    def test_add_645_minutes(self):
        # 645 min = 10h 45m  →  11:30 + 10:45 = 22:15 UTC
        result = add_time_delta(BASE_UTC, minutes=645, output_tz="UTC")
        self.assertEqual(result["iso8601"], "2025-11-16T22:15:00+00:00")
        expected_unix = BASE_UTC.timestamp() + 645 * 60
        self.assertAlmostEqual(result["unix"], expected_unix, places=3)

    def test_add_1_minute(self):
        result = add_time_delta(BASE_UTC, minutes=1, output_tz="UTC")
        self.assertEqual(result["iso8601"], "2025-11-16T11:31:00+00:00")

    def test_add_negative_minutes(self):
        result = add_time_delta(BASE_UTC, minutes=-30, output_tz="UTC")
        self.assertEqual(result["iso8601"], "2025-11-16T11:00:00+00:00")


class TestHoursAddition(unittest.TestCase):
    """Hour-level arithmetic is exact."""

    def test_add_7_hours(self):
        # 11:30 + 7h = 18:30 UTC
        result = add_time_delta(BASE_UTC, hours=7, output_tz="UTC")
        self.assertEqual(result["iso8601"], "2025-11-16T18:30:00+00:00")

    def test_add_negative_hours(self):
        result = add_time_delta(BASE_UTC, hours=-11, output_tz="UTC")
        self.assertEqual(result["iso8601"], "2025-11-16T00:30:00+00:00")


class TestDaysAddition(unittest.TestCase):
    """Day-level arithmetic crosses date boundaries correctly."""

    def test_add_1_day(self):
        result = add_time_delta(BASE_UTC, days=1, output_tz="UTC")
        self.assertEqual(result["iso8601"], "2025-11-17T11:30:00+00:00")

    def test_add_21_days(self):
        result = add_time_delta(BASE_UTC, days=21, output_tz="UTC")
        self.assertEqual(result["iso8601"], "2025-12-07T11:30:00+00:00")

    def test_add_negative_days(self):
        result = add_time_delta(BASE_UTC, days=-16, output_tz="UTC")
        # 2025-11-16 – 16 days = 2025-10-31
        self.assertEqual(result["iso8601"], "2025-10-31T11:30:00+00:00")


class TestCombinedDelta(unittest.TestCase):
    """Combined days + hours + minutes addition (the primary use case)."""

    def test_645_minutes_plus_7_hours(self):
        # 645 min = 10h 45m;  10h 45m + 7h = 17h 45m
        # 11:30 + 17h 45m = 05:15 next day (UTC)
        result = add_time_delta(BASE_UTC, minutes=645, hours=7, output_tz="UTC")
        self.assertEqual(result["iso8601"], "2025-11-17T05:15:00+00:00")
        expected_unix = BASE_UTC.timestamp() + (645 + 7 * 60) * 60
        self.assertAlmostEqual(result["unix"], expected_unix, places=3)

    def test_days_hours_minutes(self):
        result = add_time_delta(BASE_UTC, days=3, hours=9, minutes=15, output_tz="UTC")
        # 3 days + 9h 15m → 11:30 + 3d + 9h15m = 2025-11-19T20:45:00Z
        self.assertEqual(result["iso8601"], "2025-11-19T20:45:00+00:00")


class TestTimezoneConversion(unittest.TestCase):
    """Output timezone conversions are correct."""

    def test_utc_output(self):
        result = add_time_delta(BASE_UTC, output_tz="UTC")
        self.assertIn("+00:00", result["iso8601"])

    def test_et_output_november(self):
        # In November EST is UTC-5
        result = add_time_delta(BASE_UTC, output_tz="ET")
        self.assertIn("-05:00", result["iso8601"])

    def test_edt_alias_same_as_et(self):
        r_et = add_time_delta(BASE_UTC, output_tz="ET")
        r_edt = add_time_delta(BASE_UTC, output_tz="EDT")
        self.assertEqual(r_et["iso8601"], r_edt["iso8601"])
        self.assertEqual(r_et["unix"], r_edt["unix"])

    def test_est_alias_same_as_et(self):
        r_et = add_time_delta(BASE_UTC, output_tz="ET")
        r_est = add_time_delta(BASE_UTC, output_tz="EST")
        self.assertEqual(r_et["iso8601"], r_est["iso8601"])
        self.assertEqual(r_et["unix"], r_est["unix"])

    def test_unix_timestamp_invariant(self):
        """Unix timestamp must be identical regardless of output_tz."""
        unix_values = {
            tz: add_time_delta(BASE_UTC, hours=1, output_tz=tz)["unix"]
            for tz in TIMEZONES
        }
        first = next(iter(unix_values.values()))
        for tz, val in unix_values.items():
            with self.subTest(tz=tz):
                self.assertEqual(val, first)

    def test_dst_boundary_summer(self):
        # July → EDT = UTC-4
        summer_base = datetime(2025, 7, 4, 12, 0, 0, tzinfo=UTC)
        result = add_time_delta(summer_base, output_tz="ET")
        self.assertIn("-04:00", result["iso8601"])
        # 12:00 UTC → 08:00 EDT
        self.assertTrue(result["iso8601"].startswith("2025-07-04T08:00:00"))


class TestEdgeCases(unittest.TestCase):
    """Edge cases: large deltas, fractional values, unknown timezone."""

    def test_large_delta(self):
        # Add 10,000 hours (~416+ days)
        result = add_time_delta(BASE_UTC, hours=10000, output_tz="UTC")
        expected = BASE_UTC + timedelta(hours=10000)
        self.assertEqual(result["unix"], expected.timestamp())

    def test_fractional_hours(self):
        # 0.5 hours = 30 minutes
        result = add_time_delta(BASE_UTC, hours=0.5, output_tz="UTC")
        self.assertEqual(result["iso8601"], "2025-11-16T12:00:00+00:00")

    def test_fractional_minutes(self):
        # 0.5 minutes = 30 seconds
        result = add_time_delta(BASE_UTC, minutes=0.5, output_tz="UTC")
        self.assertEqual(result["iso8601"], "2025-11-16T11:30:30+00:00")

    def test_unknown_timezone_raises(self):
        with self.assertRaises(ValueError) as ctx:
            add_time_delta(BASE_UTC, output_tz="PST")
        self.assertIn("PST", str(ctx.exception))

    def test_aware_non_utc_input(self):
        # Input in Eastern time should still produce correct UTC output.
        et_base = datetime(2025, 11, 16, 6, 30, 0, tzinfo=ET)  # = 11:30 UTC
        result_from_et = add_time_delta(et_base, hours=1, output_tz="UTC")
        result_from_utc = add_time_delta(BASE_UTC, hours=1, output_tz="UTC")
        self.assertEqual(result_from_et["unix"], result_from_utc["unix"])


class TestUnixTimestamp(unittest.TestCase):
    """Unix timestamp values are correct absolute POSIX times."""

    def test_known_unix_value(self):
        # 2025-11-16T11:30:00Z → known POSIX value
        result = add_time_delta(BASE_UTC, output_tz="UTC")
        self.assertEqual(result["unix"], BASE_UTC.timestamp())

    def test_unix_increases_with_positive_delta(self):
        r1 = add_time_delta(BASE_UTC, hours=1)
        r2 = add_time_delta(BASE_UTC, hours=2)
        self.assertGreater(r2["unix"], r1["unix"])

    def test_unix_decreases_with_negative_delta(self):
        r1 = add_time_delta(BASE_UTC, hours=-1)
        self.assertLess(r1["unix"], BASE_UTC.timestamp())


# ---------------------------------------------------------------------------
# Mission timeline tests
# ---------------------------------------------------------------------------

LAUNCH_UTC = datetime(2025, 11, 16, 6, 14, tzinfo=UTC)


class TestMissionTimeline(unittest.TestCase):
    """Tests for mission_timeline.project_timeline."""

    def test_returns_all_events(self):
        timeline = project_timeline(LAUNCH_UTC)
        self.assertEqual(len(timeline), len(MISSION_EVENTS))

    def test_first_event_equals_launch(self):
        timeline = project_timeline(LAUNCH_UTC)
        first = timeline[0]
        self.assertEqual(first["unix"], LAUNCH_UTC.timestamp())
        self.assertEqual(first["iso8601_utc"], "2025-11-16T06:14:00+00:00")

    def test_events_are_ordered(self):
        timeline = project_timeline(LAUNCH_UTC)
        unix_times = [ev["unix"] for ev in timeline]
        self.assertEqual(unix_times, sorted(unix_times))

    def test_splashdown_after_21_days(self):
        timeline = project_timeline(LAUNCH_UTC)
        splashdown = timeline[-1]
        # Should be roughly 21 days + some hours after launch
        elapsed_days = (splashdown["unix"] - LAUNCH_UTC.timestamp()) / 86400
        self.assertGreater(elapsed_days, 21)

    def test_tli_event_about_90_minutes_after_launch(self):
        timeline = project_timeline(LAUNCH_UTC)
        tli = next(ev for ev in timeline if "Trans-Lunar Injection" in ev["event"])
        elapsed_minutes = (tli["unix"] - LAUNCH_UTC.timestamp()) / 60
        self.assertAlmostEqual(elapsed_minutes, 90, delta=5)

    def test_iso8601_utc_and_et_differ_in_november(self):
        timeline = project_timeline(LAUNCH_UTC)
        launch_event = timeline[0]
        # UTC+0 vs EST UTC-5: the strings differ
        self.assertNotEqual(
            launch_event["iso8601_utc"], launch_event["iso8601_et"]
        )
        self.assertIn("+00:00", launch_event["iso8601_utc"])
        self.assertIn("-05:00", launch_event["iso8601_et"])

    def test_naive_launch_treated_as_utc(self):
        naive_launch = datetime(2025, 11, 16, 6, 14)
        timeline_naive = project_timeline(naive_launch)
        timeline_aware = project_timeline(LAUNCH_UTC)
        for ev_n, ev_a in zip(timeline_naive, timeline_aware):
            self.assertEqual(ev_n["unix"], ev_a["unix"])

    def test_print_timeline_runs_without_error(self):
        import io
        import sys
        captured = io.StringIO()
        sys.stdout = captured
        try:
            print_timeline(LAUNCH_UTC)
        finally:
            sys.stdout = sys.__stdout__
        output = captured.getvalue()
        self.assertIn("Artemis II Mission Timeline", output)
        self.assertIn("Launch", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
