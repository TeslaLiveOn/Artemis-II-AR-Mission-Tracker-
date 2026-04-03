"""
mission_timeline.py
===================
Artemis II mission timeline projections using :func:`add_time_delta`.

This module provides a collection of pre-defined Artemis II mission events
relative to a configurable launch time, and a helper function to project
the full timeline given any launch datetime.

Typical usage
-------------
>>> from datetime import datetime, timezone
>>> from mission_time.mission_timeline import project_timeline, MISSION_EVENTS
>>> launch = datetime(2025, 11, 16, 6, 14, tzinfo=timezone.utc)  # planned NET
>>> timeline = project_timeline(launch)
>>> for event in timeline:
...     print(f"{event['event']:<45} {event['iso8601_utc']}")

Reference
---------
Event offsets are based on publicly available Artemis II mission documentation.
All durations are approximate and may change with mission planning updates.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TypedDict

from mission_time.timestamp_utils import add_time_delta, TIMEZONES

# ---------------------------------------------------------------------------
# Mission event definitions
# ---------------------------------------------------------------------------

class MissionEvent(TypedDict):
    """A single mission milestone with its offset from launch."""

    event: str
    """Human-readable event description."""

    days: float
    """Days after launch (may be fractional)."""

    hours: float
    """Hours after launch (added on top of *days*)."""

    minutes: float
    """Minutes after launch (added on top of *days* + *hours*)."""


#: Ordered list of Artemis II mission events with approximate offsets from
#: launch (T+0).  Offsets are additive: ``total = days*24h + hours + minutes``.
MISSION_EVENTS: list[MissionEvent] = [
    MissionEvent(event="T+0:00 – Launch / SLS liftoff",                     days=0,  hours=0,  minutes=0),
    MissionEvent(event="T+0:08 – SLS core stage separation",                days=0,  hours=0,  minutes=8),
    MissionEvent(event="T+0:12 – ICPS / Orion separation",                  days=0,  hours=0,  minutes=12),
    MissionEvent(event="T+0:22 – Perigee raise maneuver (PRM)",             days=0,  hours=0,  minutes=22),
    MissionEvent(event="T+1:30 – Trans-Lunar Injection (TLI)",              days=0,  hours=1,  minutes=30),
    MissionEvent(event="T+2:00 – Orion/ICPS separation post-TLI",          days=0,  hours=2,  minutes=0),
    MissionEvent(event="T+8:00 – Outbound Trajectory Correction 1 (OTC-1)", days=0,  hours=8,  minutes=0),
    MissionEvent(event="T+1d 0:00 – Mid-Course Correction 1 (MCC-1)",      days=1,  hours=0,  minutes=0),
    MissionEvent(event="T+3d 21:00 – Lunar Flyby (~8,900 km)",             days=3,  hours=21, minutes=0),
    MissionEvent(event="T+5d 0:00 – Distant Retrograde Orbit insertion",    days=5,  hours=0,  minutes=0),
    MissionEvent(event="T+7d 12:00 – DRO apoapsis / crew science ops",     days=7,  hours=12, minutes=0),
    MissionEvent(event="T+9d 0:00 – Distant Retrograde Orbit departure",    days=9,  hours=0,  minutes=0),
    MissionEvent(event="T+12d 9:00 – Return Powered Flyby (RPF)",          days=12, hours=9,  minutes=0),
    MissionEvent(event="T+13d 0:00 – Trans-Earth Injection (TEI)",         days=13, hours=0,  minutes=0),
    MissionEvent(event="T+15d 0:00 – Mid-Course Correction 2 (MCC-2)",     days=15, hours=0,  minutes=0),
    MissionEvent(event="T+21d 9:45 – Entry Interface (~400,000 ft)",        days=21, hours=9,  minutes=45),
    MissionEvent(event="T+21d 10:05 – Splashdown (Pacific Ocean)",         days=21, hours=10, minutes=5),
]


class ProjectedEvent(TypedDict):
    """A mission event projected to a concrete UTC and local timestamp."""

    event: str
    iso8601_utc: str
    iso8601_et: str
    unix: float


def project_timeline(
    launch_time: datetime,
    local_tz: str = "ET",
) -> list[ProjectedEvent]:
    """Return all mission events projected from *launch_time*.

    Parameters
    ----------
    launch_time:
        Planned launch datetime.  Naive datetimes are treated as UTC.
    local_tz:
        Timezone key from :data:`TIMEZONES` used for the ``iso8601_et``
        field.  Defaults to ``"ET"`` (Eastern Time, DST-aware).

    Returns
    -------
    list[ProjectedEvent]
        Ordered list of mission events with UTC and local timestamps.
    """
    results: list[ProjectedEvent] = []
    for ev in MISSION_EVENTS:
        utc_result = add_time_delta(
            launch_time,
            days=ev["days"],
            hours=ev["hours"],
            minutes=ev["minutes"],
            output_tz="UTC",
        )
        et_result = add_time_delta(
            launch_time,
            days=ev["days"],
            hours=ev["hours"],
            minutes=ev["minutes"],
            output_tz=local_tz,
        )
        results.append(
            ProjectedEvent(
                event=ev["event"],
                iso8601_utc=utc_result["iso8601"],
                iso8601_et=et_result["iso8601"],
                unix=utc_result["unix"],
            )
        )
    return results


def print_timeline(launch_time: datetime, local_tz: str = "ET") -> None:
    """Print the full projected Artemis II mission timeline to stdout.

    Parameters
    ----------
    launch_time:
        Planned launch datetime.
    local_tz:
        Local timezone label for the right-hand column.
    """
    timeline = project_timeline(launch_time, local_tz=local_tz)
    col_width = 47
    header = f"{'Mission Event':<{col_width}}  {'UTC':<25}  {local_tz}"
    print("=" * len(header))
    print(f"  Artemis II Mission Timeline (Launch: {launch_time.isoformat()})")
    print("=" * len(header))
    print(header)
    print("-" * len(header))
    for ev in timeline:
        print(
            f"{ev['event']:<{col_width}}  "
            f"{ev['iso8601_utc']:<25}  "
            f"{ev['iso8601_et']}"
        )
    print("=" * len(header))


if __name__ == "__main__":
    # Example: planned Artemis II launch NET November 2025
    launch = datetime(2025, 11, 16, 6, 14, tzinfo=timezone.utc)
    print_timeline(launch, local_tz="ET")
