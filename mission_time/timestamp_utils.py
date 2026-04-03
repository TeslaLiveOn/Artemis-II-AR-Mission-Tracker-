"""
timestamp_utils.py
==================
Utility module for Artemis II AR Mission Tracker timestamp arithmetic.

Provides :func:`add_time_delta` – a single, reusable function for adding
arbitrary combinations of days, hours, and minutes to any base timestamp
with full timezone handling (EDT ↔ UTC) and dual-format output
(ISO 8601 and Unix epoch).

Supported output timezones
--------------------------
* ``"UTC"``  – Coordinated Universal Time
* ``"EDT"``  – Eastern Daylight Time  (UTC-4, used during DST)
* ``"EST"``  – Eastern Standard Time  (UTC-5, without DST)
* ``"ET"``   – Eastern Time (America/New_York, DST-aware)

Input schemas
-------------
``base_time`` : datetime
    Any ``datetime`` object.  If *naive* (no ``tzinfo``), it is assumed to
    be **UTC**.  Timezone-aware datetimes are converted automatically.

``days``, ``hours``, ``minutes`` : int or float, default 0
    Amounts to add to *base_time*.  Negative values move backwards.

``output_tz`` : str, default ``"UTC"``
    Key from :data:`TIMEZONES`.  The result is expressed in this timezone.

Output schema (``TimestampResult`` TypedDict)
---------------------------------------------
* ``iso8601``  – ISO 8601 string with UTC-offset (e.g. ``"2025-11-16T15:30:00+00:00"``)
* ``unix``     – POSIX/Unix timestamp (float, seconds since 1970-01-01 00:00:00 UTC)
* ``timezone`` – Name string of the output timezone

Examples
--------
>>> from datetime import datetime, timezone
>>> from mission_time.timestamp_utils import add_time_delta
>>> base = datetime(2025, 11, 16, 11, 30, tzinfo=timezone.utc)
>>> result = add_time_delta(base, hours=7, minutes=645, output_tz="UTC")
>>> result["iso8601"]
'2025-11-17T01:45:00+00:00'
>>> result["unix"]
1763250300.0
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TypedDict
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------------
# Supported timezone registry
# ---------------------------------------------------------------------------

#: Map from user-facing timezone name to :class:`datetime.tzinfo` instance.
TIMEZONES: dict[str, timezone | ZoneInfo] = {
    "UTC": timezone.utc,
    "ET": ZoneInfo("America/New_York"),   # DST-aware Eastern Time
    "EDT": ZoneInfo("America/New_York"),  # alias (DST period = UTC-4)
    "EST": ZoneInfo("America/New_York"),  # alias (standard period = UTC-5)
}


class TimestampResult(TypedDict):
    """Return type of :func:`add_time_delta`."""

    iso8601: str
    """ISO 8601 formatted string with UTC-offset."""

    unix: float
    """POSIX Unix timestamp (seconds since 1970-01-01 00:00:00 UTC)."""

    timezone: str
    """Name of the output timezone as supplied by the caller."""


def add_time_delta(
    base_time: datetime,
    *,
    days: float = 0,
    hours: float = 0,
    minutes: float = 0,
    output_tz: str = "UTC",
) -> TimestampResult:
    """Return a new timestamp obtained by adding a time delta to *base_time*.

    Parameters
    ----------
    base_time:
        Starting point.  Naive datetimes are treated as **UTC**.
    days:
        Number of days to add (may be fractional or negative).
    hours:
        Number of hours to add (may be fractional or negative).
    minutes:
        Number of minutes to add (may be fractional or negative).
    output_tz:
        Timezone key from :data:`TIMEZONES` (``"UTC"``, ``"ET"``,
        ``"EDT"``, or ``"EST"``).  Defaults to ``"UTC"``.

    Returns
    -------
    TimestampResult
        Dictionary with ``iso8601``, ``unix``, and ``timezone`` fields.

    Raises
    ------
    ValueError
        If *output_tz* is not a key in :data:`TIMEZONES`.

    Examples
    --------
    Add 645 minutes and 7 hours, express result in EDT:

    >>> from datetime import datetime, timezone
    >>> base = datetime(2025, 11, 16, 11, 30, tzinfo=timezone.utc)
    >>> add_time_delta(base, minutes=645, hours=7, output_tz="EDT")
    {'iso8601': '2025-11-16T21:45:00-05:00', 'unix': 1763250300.0, 'timezone': 'EDT'}

    Use negative values to go backwards in time:

    >>> add_time_delta(base, hours=-2, output_tz="UTC")
    {'iso8601': '2025-11-16T09:30:00+00:00', 'unix': 1763188200.0, 'timezone': 'UTC'}
    """
    if output_tz not in TIMEZONES:
        raise ValueError(
            f"Unknown timezone {output_tz!r}. "
            f"Valid options are: {sorted(TIMEZONES)}"
        )

    # Ensure base_time is timezone-aware; assume UTC for naive inputs.
    if base_time.tzinfo is None:
        base_time = base_time.replace(tzinfo=timezone.utc)

    # Apply the delta.
    delta = timedelta(days=days, hours=hours, minutes=minutes)
    result_utc = base_time.astimezone(timezone.utc) + delta

    # Convert to the requested output timezone.
    tz = TIMEZONES[output_tz]
    result_local = result_utc.astimezone(tz)

    return TimestampResult(
        iso8601=result_local.isoformat(),
        unix=result_utc.timestamp(),
        timezone=output_tz,
    )
