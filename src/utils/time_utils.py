"""
time_utils.py
-------------
Utilities for parsing times and computing free time slots
within a working day, given a list of booked meeting intervals.
"""

from datetime import datetime, timedelta, time
from typing import List, Tuple


def parse_time(s: str) -> time:
    """
    Parse a time string into a :class:`datetime.time` object.

    Accepts ``HH:MM`` and ``HH:MM:SS`` formats.

    Parameters
    ----------
    s : str
        Time string, e.g. ``"09:30"`` or ``"14:00:00"``.

    Returns
    -------
    datetime.time
    """
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(s.strip(), fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse time string: '{s}'")


def _to_minutes(t: time) -> int:
    """Convert a time to minutes since midnight."""
    return t.hour * 60 + t.minute


def _from_minutes(m: int) -> time:
    """Convert minutes since midnight back to a time object."""
    return time(m // 60, m % 60)


def get_free_slots(
    meetings: List[Tuple[time, time]],
    work_start: time,
    work_end: time,
    slot_duration: int = 60,
) -> List[Tuple[time, time]]:
    """
    Compute available (free) time slots in a working day given booked meetings.

    Parameters
    ----------
    meetings : List[Tuple[time, time]]
        List of ``(start, end)`` booked meeting intervals.  Overlapping or
        duplicate intervals are handled gracefully.
    work_start : time
        Start of the working day (e.g. ``time(9, 0)``).
    work_end : time
        End of the working day (e.g. ``time(18, 0)``).
    slot_duration : int
        Minimum free-slot size in **minutes** (default: 60).

    Returns
    -------
    List[Tuple[time, time]]
        Sorted list of ``(slot_start, slot_end)`` free intervals, each at
        least ``slot_duration`` minutes long.

    Examples
    --------
    >>> from datetime import time
    >>> meetings = [(time(10, 0), time(11, 0)), (time(13, 0), time(14, 30))]
    >>> get_free_slots(meetings, time(9, 0), time(18, 0), slot_duration=60)
    [(datetime.time(9, 0), datetime.time(10, 0)),
     (datetime.time(11, 0), datetime.time(13, 0)),
     (datetime.time(14, 30), datetime.time(18, 0))]
    """
    ws = _to_minutes(work_start)
    we = _to_minutes(work_end)

    if not meetings:
        if we - ws >= slot_duration:
            return [(work_start, work_end)]
        return []

    # Build merged union of booked blocks
    blocks = sorted((_to_minutes(s), _to_minutes(e)) for s, e in meetings)
    merged: List[Tuple[int, int]] = []
    for start, end in blocks:
        # Clamp to working hours
        start = max(start, ws)
        end   = min(end, we)
        if start >= end:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    # Find gaps between merged blocks
    free_slots: List[Tuple[time, time]] = []
    cursor = ws
    for bstart, bend in merged:
        if bstart > cursor and bstart - cursor >= slot_duration:
            free_slots.append((_from_minutes(cursor), _from_minutes(bstart)))
        cursor = max(cursor, bend)

    # Trailing gap after last meeting
    if we > cursor and we - cursor >= slot_duration:
        free_slots.append((_from_minutes(cursor), _from_minutes(we)))

    return free_slots
