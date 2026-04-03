from datetime import datetime, timedelta, timezone
import hashlib

# Base timestamp (reproducible anchor) — EDT = UTC-4
EDT = timezone(timedelta(hours=-4), name="EDT")
BASE_TIME = datetime(2026, 4, 3, 13, 8, tzinfo=EDT)  # 2026-04-03 01:08 PM EDT


def add_hours(dt, hours):
    result = dt + timedelta(hours=hours)
    print(f"Input : {dt.strftime('%Y-%m-%d %H:%M %Z')}")
    print(f"+ {hours} hours")
    print(f"Result: {result.strftime('%Y-%m-%d %H:%M %Z')} ({result.strftime('%A')})")
    print(f"ISO   : {result.isoformat()}")
    print(f"Unix  : {int(result.timestamp())}")
    return result


if __name__ == "__main__":
    add_hours(BASE_TIME, 7)

    # SHA256 verification hook (for script integrity in automation)
    with open(__file__, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    print("Script SHA256:", digest)
