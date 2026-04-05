"""Unit tests for mission_time.mission_timeline."""

import pytest
from datetime import datetime, timezone

from mission_time.mission_timeline import (
    project_timeline,
    MISSION_EVENTS,
    MissionEvent,
    ProjectedEvent,
)


class TestMissionEvents:
    def test_mission_events_non_empty(self):
        assert len(MISSION_EVENTS) > 0

    def test_mission_events_first_is_launch(self):
        first = MISSION_EVENTS[0]
        assert first["days"] == 0
        assert first["hours"] == 0
        assert first["minutes"] == 0

    def test_mission_events_all_have_required_fields(self):
        for event in MISSION_EVENTS:
            assert "event" in event
            assert "days" in event
            assert "hours" in event
            assert "minutes" in event

    def test_mission_events_all_have_non_negative_offsets(self):
        for event in MISSION_EVENTS:
            assert event["days"] >= 0
            assert event["hours"] >= 0
            assert event["minutes"] >= 0

    def test_mission_events_splashdown_is_last(self):
        last = MISSION_EVENTS[-1]
        assert "Splashdown" in last["event"] or last["days"] == max(
            e["days"] for e in MISSION_EVENTS
        )

    def test_mission_events_contains_tli(self):
        event_names = [e["event"] for e in MISSION_EVENTS]
        assert any("Trans-Lunar" in name or "TLI" in name for name in event_names)

    def test_mission_events_contains_lunar_flyby(self):
        event_names = [e["event"] for e in MISSION_EVENTS]
        assert any("Lunar Flyby" in name or "Flyby" in name for name in event_names)


class TestProjectTimeline:
    def setup_method(self):
        self.launch = datetime(2025, 11, 16, 6, 14, tzinfo=timezone.utc)

    def test_returns_list(self):
        timeline = project_timeline(self.launch)
        assert isinstance(timeline, list)

    def test_returns_correct_number_of_events(self):
        timeline = project_timeline(self.launch)
        assert len(timeline) == len(MISSION_EVENTS)

    def test_each_event_has_required_fields(self):
        timeline = project_timeline(self.launch)
        for event in timeline:
            assert "event" in event
            assert "iso8601_utc" in event
            assert "iso8601_et" in event
            assert "unix" in event

    def test_first_event_matches_launch_time(self):
        timeline = project_timeline(self.launch, local_tz="UTC")
        first = timeline[0]
        assert first["iso8601_utc"] == "2025-11-16T06:14:00+00:00"

    def test_unix_timestamps_are_monotonically_increasing(self):
        timeline = project_timeline(self.launch)
        unix_times = [e["unix"] for e in timeline]
        assert unix_times == sorted(unix_times)

    def test_event_names_preserved(self):
        timeline = project_timeline(self.launch)
        for projected, original in zip(timeline, MISSION_EVENTS):
            assert projected["event"] == original["event"]

    def test_utc_iso8601_contains_utc_offset(self):
        timeline = project_timeline(self.launch)
        for event in timeline:
            assert "+00:00" in event["iso8601_utc"]

    def test_et_iso8601_contains_eastern_offset(self):
        # November is EST (UTC-5)
        timeline = project_timeline(self.launch, local_tz="ET")
        for event in timeline:
            assert "-05:00" in event["iso8601_et"] or "-04:00" in event["iso8601_et"]

    def test_naive_launch_treated_as_utc(self):
        naive_launch = datetime(2025, 11, 16, 6, 14)  # no tzinfo
        timeline_naive = project_timeline(naive_launch, local_tz="UTC")
        timeline_aware = project_timeline(self.launch, local_tz="UTC")
        for naive_ev, aware_ev in zip(timeline_naive, timeline_aware):
            assert naive_ev["iso8601_utc"] == aware_ev["iso8601_utc"]
            assert naive_ev["unix"] == aware_ev["unix"]

    def test_known_splashdown_timestamp(self):
        # T+21d 10:05 from 2025-11-16T06:14:00Z = 2025-12-07T16:19:00Z
        timeline = project_timeline(self.launch, local_tz="UTC")
        splashdown = next(e for e in timeline if "Splashdown" in e["event"])
        assert splashdown["iso8601_utc"] == "2025-12-07T16:19:00+00:00"

    def test_invalid_local_tz_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown timezone"):
            project_timeline(self.launch, local_tz="INVALID")
