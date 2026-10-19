"""PawPal+ logic layer: Owner, Pet, Task, and Scheduler.

Phase 1 skeleton — attributes and method stubs only. Logic is filled in during Phase 2/4.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


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

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        pass

    def remove_task(self, title: str) -> None:
        """Remove a task by title."""
        pass

    def pending_tasks(self) -> list[Task]:
        """Return tasks that are not yet completed."""
        pass


@dataclass
class Owner:
    """The pet owner, their time budget, and their pets."""

    name: str
    available_minutes: int = 120
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def remove_pet(self, name: str) -> None:
        """Remove a pet by name."""
        pass

    def get_pet(self, name: str) -> Optional[Pet]:
        """Look up a pet by name."""
        pass

    def all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every (pet, task) pair across all pets."""
        pass


class Scheduler:
    """The 'brain': reads an Owner's pets/tasks and builds a daily plan."""

    def __init__(self, owner: Owner, day: Optional[date] = None) -> None:
        self.owner = owner
        self.day = day or date.today()

    def generate_plan(self) -> list[tuple[Pet, Task]]:
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

    def explain_plan(self, plan: list[tuple[Pet, Task]]) -> str:
        """Explain why tasks were chosen/skipped and in what order."""
        pass
