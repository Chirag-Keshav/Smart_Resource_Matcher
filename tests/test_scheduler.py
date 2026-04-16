"""
test_scheduler.py
-----------------
Unit tests for the Phase 4 Availability Scheduler.

Tests cover:
  - Fully booked day (no free slots)
  - Partially booked day (some free slots between meetings)
  - Completely free day (full working window)
  - Multiple employees at once
  - Custom slot duration filtering
  - Edge cases: unknown employee, string target_date, missing columns

Uses small fixture DataFrames to keep tests fast and deterministic.
"""

from datetime import date, time

import pandas as pd
import pytest

from src.scheduler.availability import get_availability


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

TARGET_DATE = date(2026, 4, 10)  # arbitrary fixed date for all tests


@pytest.fixture
def schedules_df() -> pd.DataFrame:
    """
    Fixture schedules DataFrame with three employees on TARGET_DATE:

    E001 — fully booked (09:00–18:00 covered by consecutive meetings)
    E002 — partially booked (two meetings, gaps before/between/after)
    E003 — no meetings at all (completely free)
    E004 — has meetings on *different* dates (free on TARGET_DATE)
    """
    rows = [
        # ── E001: fully booked 09:00–18:00 ────────────────────────────────
        ("E001", TARGET_DATE, "09:00", "12:00", "Morning block"),
        ("E001", TARGET_DATE, "12:00", "15:00", "Afternoon block 1"),
        ("E001", TARGET_DATE, "15:00", "18:00", "Afternoon block 2"),

        # ── E002: two meetings with gaps ──────────────────────────────────
        #   09:00-10:00 free → 10:00-11:30 booked → 11:30-14:00 free
        #   → 14:00-15:00 booked → 15:00-18:00 free
        ("E002", TARGET_DATE, "10:00", "11:30", "Standup"),
        ("E002", TARGET_DATE, "14:00", "15:00", "Review"),

        # ── E003: no meetings on TARGET_DATE ──────────────────────────────
        #   (completely free: 09:00-18:00)

        # ── E004: meetings on a different date ────────────────────────────
        ("E004", date(2026, 4, 11), "09:00", "10:00", "Other day meeting"),
    ]

    df = pd.DataFrame(rows, columns=[
        "employee_id", "date", "start_time", "end_time", "meeting_title",
    ])
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# Tests — get_availability()
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetAvailability:
    """Tests for scheduler.availability.get_availability()."""

    def test_fully_booked_day(self, schedules_df):
        """Employee with back-to-back meetings covering 09–18 has no free slots."""
        result = get_availability(["E001"], schedules_df, TARGET_DATE)

        assert "E001" in result
        assert result["E001"] == []

    def test_partially_booked_day(self, schedules_df):
        """Employee with two meetings should have three free windows."""
        result = get_availability(["E002"], schedules_df, TARGET_DATE)

        free = result["E002"]
        assert len(free) == 3

        # 09:00–10:00
        assert free[0] == (time(9, 0), time(10, 0))
        # 11:30–14:00
        assert free[1] == (time(11, 30), time(14, 0))
        # 15:00–18:00
        assert free[2] == (time(15, 0), time(18, 0))

    def test_completely_free_day(self, schedules_df):
        """Employee with no meetings gets the full working window."""
        result = get_availability(["E003"], schedules_df, TARGET_DATE)

        free = result["E003"]
        assert len(free) == 1
        assert free[0] == (time(9, 0), time(18, 0))

    def test_meetings_on_different_date(self, schedules_df):
        """Meetings on other dates should not affect target_date availability."""
        result = get_availability(["E004"], schedules_df, TARGET_DATE)

        free = result["E004"]
        assert len(free) == 1
        assert free[0] == (time(9, 0), time(18, 0))

    def test_multiple_employees(self, schedules_df):
        """Should compute availability for all requested employees at once."""
        result = get_availability(
            ["E001", "E002", "E003"], schedules_df, TARGET_DATE,
        )

        assert len(result) == 3
        assert result["E001"] == []
        assert len(result["E002"]) == 3
        assert len(result["E003"]) == 1

    def test_unknown_employee(self, schedules_df):
        """An employee not in the schedules should be treated as fully free."""
        result = get_availability(["E999"], schedules_df, TARGET_DATE)

        assert "E999" in result
        assert len(result["E999"]) == 1
        assert result["E999"][0] == (time(9, 0), time(18, 0))

    def test_custom_slot_duration(self, schedules_df):
        """With a large slot_duration, small gaps should be filtered out."""
        # E002 has a 1-hour gap at 09:00–10:00.
        # Setting slot_duration=90 should exclude that gap.
        result = get_availability(
            ["E002"], schedules_df, TARGET_DATE, slot_duration=90,
        )

        free = result["E002"]
        # Only the two larger gaps should remain:
        #   11:30–14:00 (150 min) and 15:00–18:00 (180 min)
        assert len(free) == 2
        assert free[0] == (time(11, 30), time(14, 0))
        assert free[1] == (time(15, 0), time(18, 0))

    def test_string_target_date(self, schedules_df):
        """target_date can be passed as a string and should be auto-parsed."""
        result = get_availability(
            ["E002"], schedules_df, "2026-04-10",
        )

        assert len(result["E002"]) == 3  # same as date object

    def test_empty_employee_list(self, schedules_df):
        """An empty employee list should return an empty dict."""
        result = get_availability([], schedules_df, TARGET_DATE)

        assert result == {}

    def test_missing_columns_raises(self):
        """Should raise ValueError when schedules_df lacks required columns."""
        bad_df = pd.DataFrame({"employee_id": ["E001"], "name": ["Alice"]})

        with pytest.raises(ValueError, match="missing required columns"):
            get_availability(["E001"], bad_df, TARGET_DATE)

    def test_overlapping_meetings(self):
        """Overlapping meeting intervals should be merged correctly."""
        df = pd.DataFrame({
            "employee_id": ["E001", "E001"],
            "date": [TARGET_DATE, TARGET_DATE],
            "start_time": ["10:00", "10:30"],
            "end_time": ["11:30", "12:00"],
            "meeting_title": ["Meeting A", "Meeting B"],
        })

        result = get_availability(["E001"], df, TARGET_DATE)
        free = result["E001"]

        # Merged block: 10:00–12:00
        # Free: 09:00–10:00, 12:00–18:00
        assert len(free) == 2
        assert free[0] == (time(9, 0), time(10, 0))
        assert free[1] == (time(12, 0), time(18, 0))
