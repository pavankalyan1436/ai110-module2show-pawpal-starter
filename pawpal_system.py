"""PawPal+ logic layer: Owner, Pet, Task, Plan, and Scheduler."""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from typing import Optional
from uuid import uuid4


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
FREQUENCIES = {"once", "daily", "weekly"}
RECURRENCE_DAYS = {"daily": 1, "weekly": 7}
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
        self.completed = True

    def priority_rank(self) -> int:
        """Return a sortable number for priority (lower = more urgent)."""
        return PRIORITY_ORDER[self.priority]

    def next_occurrence(self) -> Optional["Task"]:
        """For recurring tasks, return a new Task for the next due date; else None."""
        days = RECURRENCE_DAYS.get(self.frequency)
        if days is None:
            return None
        return replace(
            self,
            due_date=self.due_date + timedelta(days=days),
            completed=False,
            id=_new_id(),
        )


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
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a task by id."""
        self.tasks = [t for t in self.tasks if t.id != task_id]

    def get_task(self, task_id: str) -> Optional[Task]:
        """Look up a task by id."""
        return next((t for t in self.tasks if t.id == task_id), None)

    def complete_task(self, task_id: str) -> Optional[Task]:
        """Mark a task done and append its next occurrence (if recurring).

        Returns the newly created occurrence, or None. Safe to call twice:
        completing an already-completed task is a no-op and creates nothing.
        Unknown ids also return None.
        """
        task = self.get_task(task_id)
        if task is None or task.completed:
            return None
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            self.add_task(next_task)
        return next_task

    def pending_tasks(self) -> list[Task]:
        """Return tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    """The pet owner, their time budget, and their pets."""

    name: str
    available_minutes: int = 120
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        """Remove a pet by id."""
        self.pets = [p for p in self.pets if p.id != pet_id]

    def get_pet(self, pet_id: str) -> Optional[Pet]:
        """Look up a pet by id."""
        return next((p for p in self.pets if p.id == pet_id), None)

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every (pet, task) pair across all pets."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


@dataclass
class Plan:
    """The result of scheduling: what made it in, what didn't (and why)."""

    scheduled: list[tuple[Pet, Task]] = field(default_factory=list)
    skipped: list[tuple[Pet, Task, str]] = field(default_factory=list)  # (pet, task, reason)
    minutes_used: int = 0


class Scheduler:
    """The 'brain': reads an Owner's pets/tasks and builds a daily plan.

    All task access goes through self.owner.get_all_tasks().
    """

    def __init__(self, owner: Owner, day: Optional[date] = None) -> None:
        self.owner = owner
        self.day = day or date.today()

    def generate_plan(self) -> Plan:
        """Pick and order today's tasks so they fit within the owner's available time.

        Candidates are incomplete tasks due on or before self.day. They are chosen
        greedily by priority (shorter first on ties); a task that doesn't fit is
        skipped and the next one is tried. Scheduled tasks are returned in time order.
        """
        due = [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if not task.completed and task.due_date <= self.day
        ]

        plan = Plan()
        remaining = self.owner.available_minutes
        for pet, task in self.sort_by_priority(due):
            if task.duration_minutes <= remaining:
                plan.scheduled.append((pet, task))
                remaining -= task.duration_minutes
            else:
                reason = f"not enough time (needs {task.duration_minutes} min, {remaining} min left)"
                plan.skipped.append((pet, task, reason))

        plan.scheduled = self.sort_by_time(plan.scheduled)
        plan.minutes_used = self.owner.available_minutes - remaining
        return plan

    def sort_by_priority(self, tasks: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Order tasks high -> low priority (ties broken by shorter duration)."""
        return sorted(tasks, key=lambda pt: (pt[1].priority_rank(), pt[1].duration_minutes))

    def sort_by_time(self, tasks: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Order tasks by their HH:MM start time; untimed tasks go last."""
        # Zero-padded "HH:MM" strings sort correctly as text (enforced in Task.__post_init__).
        return sorted(tasks, key=lambda pt: (pt[1].time is None, pt[1].time or ""))

    def filter_tasks(
        self, pet_name: Optional[str] = None, completed: Optional[bool] = None
    ) -> list[tuple[Pet, Task]]:
        """Filter tasks by pet and/or completion status."""
        return [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if (pet_name is None or pet.name == pet_name)
            and (completed is None or task.completed == completed)
        ]

    def detect_conflicts(self, tasks: list[tuple[Pet, Task]]) -> list[str]:
        """Return human-readable warnings for timed tasks that share a start time.

        Only exact start-time matches are flagged for now; duration overlaps are not.
        """
        by_time: dict[str, list[tuple[Pet, Task]]] = {}
        for pet, task in tasks:
            if task.time is not None:
                by_time.setdefault(task.time, []).append((pet, task))

        warnings = []
        for time, group in sorted(by_time.items()):
            if len(group) > 1:
                names = ", ".join(f"{task.title} ({pet.name})" for pet, task in group)
                warnings.append(f"Conflict at {time}: {names}")
        return warnings

    def explain_plan(self, plan: Plan) -> str:
        """Explain why tasks were chosen/skipped and in what order."""
        lines = [
            f"Plan for {self.day.isoformat()}: "
            f"{plan.minutes_used} of {self.owner.available_minutes} min used",
            "Tasks were picked by priority (high first, shorter first on ties), "
            "then listed by start time (untimed last).",
            "",
            "Scheduled:",
        ]
        if plan.scheduled:
            for pet, task in plan.scheduled:
                start = task.time or "--:--"
                lines.append(
                    f"  {start}  {task.title} ({pet.name}) - "
                    f"{task.duration_minutes} min [{task.priority}]"
                )
        else:
            lines.append("  (nothing scheduled)")

        lines += ["", "Skipped:"]
        if plan.skipped:
            for pet, task, reason in plan.skipped:
                lines.append(f"  {task.title} ({pet.name}) [{task.priority}]: {reason}")
        else:
            lines.append("  (nothing skipped)")

        conflicts = self.detect_conflicts(plan.scheduled)
        if conflicts:
            lines += ["", "Warnings:"] + [f"  {c}" for c in conflicts]
        return "\n".join(lines)
