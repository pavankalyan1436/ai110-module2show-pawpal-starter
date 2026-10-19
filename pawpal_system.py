"""PawPal+ logic layer: Owner, Pet, Task, Plan, and Scheduler.

Phase 1 skeleton — attributes and method stubs only. Logic is filled in during Phase 2/4.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from uuid import uuid4


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
FREQUENCIES = {"once", "daily", "weekly"}
TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")  # zero-padded 24h "HH:MM"


def _new_id() -> str:
    return uuid4().hex


@dataclass
class Task:
    """A single pet care activity (walk, feeding, meds, appointment, ...)."""

    title: str
    duration_minutes: int
    priority: str = "medium"          # "high" | "medium" | "low"
    category: str = "general"         # walk, feeding, meds, grooming, enrichment, appointment
    time: Optional[str] = None        # preferred start time, "HH:MM"
    frequency: str = "once"           # "once" | "daily" | "weekly"
    due_date: date = field(default_factory=date.today)
    completed: bool = False
    id: str = field(default_factory=_new_id)

    def __post_init__(self) -> None:
        """Reject invalid priority, frequency, or time values at creation."""
        if self.priority not in PRIORITY_ORDER:
            raise ValueError(
                f"priority must be one of {sorted(PRIORITY_ORDER)}, got {self.priority!r}"
            )
        if self.frequency not in FREQUENCIES:
            raise ValueError(
                f"frequency must be one of {sorted(FREQUENCIES)}, got {self.frequency!r}"
            )
        if self.time is not None and not TIME_PATTERN.match(self.time):
            raise ValueError(f'time must be zero-padded "HH:MM" (e.g. "09:05"), got {self.time!r}')

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass

    def priority_rank(self) -> int:
        """Return a sortable number for priority (lower = more urgent)."""
        pass

    def next_occurrence(self) -> Optional["Task"]:
        """For recurring tasks, return a new Task for the next due date; else None."""
        pass


@dataclass
class Pet:
    """A pet and the care tasks that belong to it."""

    name: str
    species: str
    breed: str = ""
    age: int = 0
    tasks: list[Task] = field(default_factory=list)
    id: str = field(default_factory=_new_id)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        pass

    def remove_task(self, task_id: str) -> None:
        """Remove a task by id."""
        pass

    def get_task(self, task_id: str) -> Optional[Task]:
        """Look up a task by id."""
        pass

    def complete_task(self, task_id: str) -> Optional[Task]:
        """Mark a task done and append its next occurrence (if recurring).

        Returns the newly created occurrence, or None. Safe to call twice:
        completing an already-completed task is a no-op and creates nothing.
        """
        pass

    def pending_tasks(self) -> list[Task]:
        """Return tasks that are not yet completed."""
        pass


@dataclass
class Owner:
    """The pet owner, their time budget, and their pets."""

    name: str
    available_minutes: int = 120
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def remove_pet(self, pet_id: str) -> None:
        """Remove a pet by id."""
        pass

    def get_pet(self, pet_id: str) -> Optional[Pet]:
        """Look up a pet by id."""
        pass

    def all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every (pet, task) pair across all pets."""
        pass


@dataclass
class Plan:
    """The result of scheduling: what made it in, what didn't (and why)."""

    scheduled: list[tuple[Pet, Task]] = field(default_factory=list)
    skipped: list[tuple[Pet, Task, str]] = field(default_factory=list)  # (pet, task, reason)
    minutes_used: int = 0


class Scheduler:
    """The 'brain': reads an Owner's pets/tasks and builds a daily plan."""

    def __init__(self, owner: Owner, day: Optional[date] = None) -> None:
        self.owner = owner
        self.day = day or date.today()

    def generate_plan(self) -> Plan:
        """Pick and order today's tasks so they fit within the owner's available time."""
        pass

    def sort_by_priority(self, tasks: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Order tasks high -> low priority (ties broken by shorter duration)."""
        pass

    def sort_by_time(self, tasks: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Order tasks by their HH:MM start time; untimed tasks go last."""
        pass

    def filter_tasks(
        self, pet_name: Optional[str] = None, completed: Optional[bool] = None
    ) -> list[tuple[Pet, Task]]:
        """Filter tasks by pet and/or completion status."""
        pass

    def detect_conflicts(self, tasks: list[tuple[Pet, Task]]) -> list[str]:
        """Return human-readable warnings for tasks with overlapping time slots."""
        pass

    def explain_plan(self, plan: Plan) -> str:
        """Explain why tasks were chosen/skipped and in what order."""
        pass
