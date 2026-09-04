"""Recurrence utilities — timezone-aware python-dateutil wrapper.

Shared by chores, bills, maintenance. Stores rrule as RFC5545 string
with a tz-aware dtstart (household timezone, stored UTC, rendered in tz).
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from dateutil.rrule import rrulestr  # type: ignore[import-untyped]


def next_due(rrule_str: str, after: datetime, tz: ZoneInfo) -> datetime | None:
    """Return next occurrence after `after` (tz-aware)."""
    # rrulestr expects DTSTART in rrule; we pass via dtstart param if missing
    # Ensure after is tz-aware
    if after.tzinfo is None:
        after = after.replace(tzinfo=tz)
    # Build rule — dateutil parses FREQ etc.
    rule = rrulestr(rrule_str, dtstart=after)
    nxt = rule.after(after, inc=False)
    if nxt and nxt.tzinfo is None:
        nxt = nxt.replace(tzinfo=tz)
    return nxt


def describe_rrule(rrule_str: str) -> str:
    """Human description — lightweight; expand later with dateutil."""
    return rrule_str
