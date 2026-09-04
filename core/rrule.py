"""Recurrence utilities — timezone-aware python-dateutil wrapper.

Shared by chores, bills, maintenance. Stores rrule as RFC5545 string
with a tz-aware dtstart (household timezone, stored UTC, rendered in tz).
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from dateutil.rrule import rrulestr  # type: ignore[import-untyped]


def next_due(
    rrule_str: str, after: datetime, tz: ZoneInfo, dtstart: datetime | None = None
) -> datetime | None:
    """Return next occurrence after `after` (tz-aware).

    If dtstart is provided, use it as the series start; otherwise use `after`.
    Handles DTSTART in rrule_str if present.
    """
    if after.tzinfo is None:
        after = after.replace(tzinfo=tz)
    if dtstart is not None and dtstart.tzinfo is None:
        dtstart = dtstart.replace(tzinfo=tz)
    # If no dtstart given, use after as dtstart (preserves clock time)
    dtstart = dtstart or after
    # If rrule_str already contains DTSTART, rrulestr will use it
    rule = rrulestr(rrule_str, dtstart=dtstart)
    nxt = rule.after(after, inc=False)
    if nxt and nxt.tzinfo is None:
        nxt = nxt.replace(tzinfo=tz)
    return nxt


def describe_rrule(rrule_str: str) -> str:
    """Human description — lightweight; expand later with dateutil."""
    return rrule_str
