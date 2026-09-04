from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from core.rrule import next_due

pytestmark = pytest.mark.django_db


def test_next_due_weekly():
    tz = ZoneInfo("Europe/Berlin")
    dtstart = datetime(2026, 1, 5, 7, 0, tzinfo=tz)  # Monday 07:00
    after = datetime(2026, 1, 5, 7, 1, tzinfo=tz)
    nxt = next_due("FREQ=WEEKLY;BYDAY=MO", after, tz, dtstart=dtstart)
    assert nxt == datetime(2026, 1, 12, 7, 0, tzinfo=tz)


def test_monthly_31_edge():
    tz = ZoneInfo("Europe/Berlin")
    dtstart = datetime(2026, 1, 31, 9, 0, tzinfo=tz)
    after = datetime(2026, 2, 1, 9, 0, tzinfo=tz)
    nxt = next_due("FREQ=MONTHLY;BYMONTHDAY=31", after, tz, dtstart=dtstart)
    # Feb has no 31, should skip to Mar 31
    assert nxt == datetime(2026, 3, 31, 9, 0, tzinfo=tz)


def test_daily():
    tz = ZoneInfo("UTC")
    dtstart = datetime(2026, 9, 5, 2, 0, tzinfo=tz)
    after = datetime(2026, 9, 5, 2, 0, tzinfo=tz)
    nxt = next_due("FREQ=DAILY", after, tz, dtstart=dtstart)
    assert nxt == datetime(2026, 9, 6, 2, 0, tzinfo=tz)


def test_dst_spring_forward():
    tz = ZoneInfo("Europe/Berlin")
    # DST 2026-03-29 02:00 missing in Berlin, rule daily at 02:00
    dtstart = datetime(2026, 3, 28, 2, 0, tzinfo=tz)
    after = datetime(2026, 3, 28, 2, 0, tzinfo=tz)
    nxt = next_due("FREQ=DAILY;BYHOUR=2", after, tz, dtstart=dtstart)
    # should not raise, and next should be 2026-03-30 02:00 (skips 29th)
    assert nxt is not None
    # next after 29th should be 30th
    after2 = datetime(2026, 3, 29, 3, 0, tzinfo=tz)
    nxt2 = next_due("FREQ=DAILY;BYHOUR=2", after2, tz, dtstart=dtstart)
    assert nxt2 == datetime(2026, 3, 30, 2, 0, tzinfo=tz)
