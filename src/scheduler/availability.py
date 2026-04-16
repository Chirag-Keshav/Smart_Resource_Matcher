"""
availability.py
---------------
Availability scheduler for the Smart Resource Matcher project.

Given a list of employee IDs, the full schedules DataFrame, and a target
date, computes each employee's free time slots within working hours
(09:00–18:00) by subtracting booked meeting intervals.
"""

from datetime import date, time
from typing import Dict, List, Tuple, Union

import pandas as pd

from src.config.settings import WORK_START, WORK_END, DEFAULT_SLOT_DURATION
from src.utils.time_utils import parse_time, get_free_slots


def get_availability(
    employee_ids: List[str],
    schedules_df: pd.DataFrame,
    target_date: Union[date, str],
    slot_duration: int = DEFAULT_SLOT_DURATION,
) -> Dict[str, List[Tuple[time, time]]]:
    """
    Compute free time slots for each employee on a given date.

    Parameters
    ----------
    employee_ids : List[str]
        Employee IDs to check availability for.
    schedules_df : pd.DataFrame
        Full schedules DataFrame as returned by ``loader.load_schedules()``.
        Must contain columns: ``employee_id``, ``date``, ``start_time``,
        ``end_time``.
    target_date : date or str
        The calendar date to check.  If a string, parsed via
        ``pd.to_datetime().date()``.
    slot_duration : int
        Minimum free-slot size in **minutes** (default from settings: 60).

    Returns
    -------
    Dict[str, List[Tuple[time, time]]]
        Mapping of ``employee_id`` → list of ``(slot_start, slot_end)``
        free intervals within working hours.  Employees with no meetings
        on the target date get the full working-hours window as a single
        slot (if it satisfies ``slot_duration``).

    Raises
    ------
    ValueError
        If ``schedules_df`` is missing required columns.

    Examples
    --------
    >>> from src.data_loader.loader import load_schedules
    >>> schedules = load_schedules()
    >>> avail = get_availability(["E001", "E002"], schedules, "2026-04-08")
    >>> avail["E001"]  # list of (start, end) free slots
    """
    # ── Validate input ────────────────────────────────────────────────────
    required_cols = {"employee_id", "date", "start_time", "end_time"}
    missing = required_cols - set(schedules_df.columns)
    if missing:
        raise ValueError(
            f"schedules_df is missing required columns: {missing}"
        )

    # ── Normalise target_date ─────────────────────────────────────────────
    if isinstance(target_date, str):
        target_date = pd.to_datetime(target_date).date()

    # ── Parse working-hours boundaries ────────────────────────────────────
    work_start = parse_time(WORK_START)
    work_end = parse_time(WORK_END)

    # ── Filter schedules to the target date ───────────────────────────────
    day_schedules = schedules_df[schedules_df["date"] == target_date]

    # ── Compute per-employee free slots ───────────────────────────────────
    availability: Dict[str, List[Tuple[time, time]]] = {}

    for emp_id in employee_ids:
        emp_meetings = day_schedules[day_schedules["employee_id"] == emp_id]

        # Build list of (start_time, end_time) tuples for this employee
        meeting_intervals: List[Tuple[time, time]] = []
        for _, row in emp_meetings.iterrows():
            try:
                m_start = parse_time(row["start_time"])
                m_end = parse_time(row["end_time"])
                meeting_intervals.append((m_start, m_end))
            except (ValueError, TypeError):
                # Skip rows with unparseable times
                continue

        # Delegate to the existing free-slot logic
        free = get_free_slots(
            meetings=meeting_intervals,
            work_start=work_start,
            work_end=work_end,
            slot_duration=slot_duration,
        )
        availability[emp_id] = free

    return availability
