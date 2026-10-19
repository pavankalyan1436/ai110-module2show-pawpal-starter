"""PawPal+ logic layer: Owner, Pet, Task, Plan, and Scheduler."""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from itertools import combinations
from typing import Optional
from uuid import uuid4


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
FREQUENCIES = {"once", "daily", "weekly"}
RECURRENCE_DAYS = {"daily": 1, "weekly": 7}
TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")  # zero-padded 24h "HH:MM"


def _new_id() -> str:
    return uuid4().hex


def _to_minutes(hhmm: str) -> int:
    """Turn "HH:MM" into minutes since midnight."""
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def _format_minutes(minutes: int) -> str:
    """Turn minutes since midnight into "HH:MM"."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


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
        """Reject invalid duration, priority, frequency, or time values at creation."""
        if self.duration_minutes <= 0:
            raise ValueError(f"duration_minutes must be positive, got {self.duration_minutes!r}")
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

    @property
    def start_minutes(self) -> Optional[int]:
        """Start time as minutes since midnight, or None if untimed."""
        return None if self.time is None else _to_minutes(self.time)

    @property
    def end_minutes(self) -> Optional[int]:
        """End time as minutes since midnight, or None if untimed."""
        start = self.start_minutes
        return None if start is None else start + self.duration_minutes

    def overlaps(self, other: "Task") -> bool:
        """True if both tasks are timed and their time ranges overlap (touching ends don't count)."""
        if self.time is None or other.time is None:
            return False
        return self.start_minutes < other.end_minutes and other.start_minutes < self.end_minutes

    def next_occurrence(self, completed_on: Optional[date] = None) -> Optional["Task"]:
        """For recurring tasks, return a new Task for the next due date; else None.

        The next due date counts from whichever is later: the old due date or the
        day it was completed. So a daily task finished 3 days late is next due
        tomorrow, not on a day that has already passed.
        """
        days = RECURRENCE_DAYS.get(self.frequency)
        if days is None:
            return None
        base = max(self.due_date, completed_on or self.due_date)
        return replace(
            self,
            due_date=base + timedelta(days=days),
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

    def complete_task(self, task_id: str, completed_on: Optional[date] = None) -> Optional[Task]:
        """Mark a task done and append its next occurrence (if recurring).

        Returns the newly created occurrence, or None. Safe to call twice:
        completing an already-completed task is a no-op and creates nothing.
        Unknown ids also return None. completed_on (default: today) sets where
        the next due date counts from; see Task.next_occurrence().
        """
        task = self.get_task(task_id)
        if task is None or task.completed:
            return None
        task.mark_complete()
        next_task = task.next_occurrence(completed_on or date.today())
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
        """Order tasks by start time; untimed tasks go last.

        Ties (same start time, or both untimed) go high -> low priority, then shorter first.
        """
        return sorted(
            tasks,
            key=lambda pt: (
                pt[1].start_minutes is None,
                pt[1].start_minutes or 0,
                pt[1].priority_rank(),
                pt[1].duration_minutes,
            ),
        )

    def filter_tasks(
        self,
        pet_id: Optional[str] = None,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
        due_by: Optional[date] = None,
    ) -> list[tuple[Pet, Task]]:
        """Filter tasks by pet, completion status, and/or due date.

        pet_id is exact; pet_name ignores case. due_by keeps tasks due on or
        before that date, which hides future occurrences of recurring tasks.
        """
        name = pet_name.casefold() if pet_name is not None else None
        return [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if (pet_id is None or pet.id == pet_id)
            and (name is None or pet.name.casefold() == name)
            and (completed is None or task.completed == completed)
            and (due_by is None or task.due_date <= due_by)
        ]

    def mark_task_complete(self, pet_id: str, task_id: str) -> Optional[Task]:
        """Complete a pet's task as of self.day; return the next occurrence, if any.

        Returns None for unknown pet/task ids, already-completed tasks, and
        one-off tasks.
        """
        pet = self.owner.get_pet(pet_id)
        if pet is None:
            return None
        return pet.complete_task(task_id, completed_on=self.day)

    def detect_conflicts(
        self, tasks: list[tuple[Pet, Task]], same_day: bool = False
    ) -> list[str]:
        """Return a warning for each pair of timed tasks whose time ranges overlap.

        See conflicting_pairs() for which tasks are compared.
        """
        return [
            f"Conflict: {self._describe(p1, t1)} overlaps {self._describe(p2, t2)}"
            for (p1, t1), (p2, t2) in self.conflicting_pairs(tasks, same_day)
        ]

    def conflicting_pairs(
        self, tasks: list[tuple[Pet, Task]], same_day: bool = False
    ) -> list[tuple[tuple[Pet, Task], tuple[Pet, Task]]]:
        """Return each pair of timed tasks whose time ranges overlap, earlier task first.

        Only incomplete tasks due on the same date are compared, unless
        same_day is True: then every task is treated as happening on self.day
        (use this for plan.scheduled, where overdue tasks are done today).
        Back-to-back tasks (one ends exactly when the next starts) are not a
        conflict, and untimed tasks are ignored. Pairs are in start-time order.
        """
        ordered = self.sort_by_time([(p, t) for p, t in tasks if not t.completed])
        return [
            (first, second)
            for first, second in combinations(ordered, 2)
            if (same_day or first[1].due_date == second[1].due_date)
            and first[1].overlaps(second[1])
        ]

    def find_next_available_slot(
        self,
        duration_minutes: int,
        day_start: str = "07:00",
        day_end: str = "21:00",
        tasks: Optional[list[tuple[Pet, Task]]] = None,
    ) -> Optional[str]:
        """Return the earliest "HH:MM" where a task of this length fits, or None.

        The slot must start at or after day_start, end by day_end, and not
        overlap any busy task (touching ends are fine). Busy tasks are the
        timed, incomplete tasks in `tasks`, which defaults to today's plan
        (generate_plan().scheduled). To find a new time for a task, pass the
        plan without that task so its current slot doesn't block it.
        """
        if duration_minutes <= 0:
            raise ValueError(f"duration_minutes must be positive, got {duration_minutes!r}")
        for bound in (day_start, day_end):
            if not TIME_PATTERN.match(bound):
                raise ValueError(f'day bounds must be zero-padded "HH:MM", got {bound!r}')
        if tasks is None:
            tasks = self.generate_plan().scheduled

        busy = sorted(
            (t.start_minutes, t.end_minutes)
            for _, t in tasks
            if t.time is not None and not t.completed
        )
        candidate = _to_minutes(day_start)
        for start, end in busy:
            if start - candidate >= duration_minutes:
                break  # the gap before this task is big enough
            candidate = max(candidate, end)
        if candidate + duration_minutes > _to_minutes(day_end):
            return None
        return _format_minutes(candidate)

    @staticmethod
    def _describe(pet: Pet, task: Task) -> str:
        """Format a timed task as "Title (Pet, HH:MM-HH:MM)" for warnings."""
        return f"{task.title} ({pet.name}, {task.time}-{_format_minutes(task.end_minutes)})"

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

        pairs = self.conflicting_pairs(plan.scheduled, same_day=True)
        if pairs:
            lines += ["", "Warnings:"]
        for (p1, t1), (p2, t2) in pairs:
            lines.append(f"  Conflict: {self._describe(p1, t1)} overlaps {self._describe(p2, t2)}")
            # Suggest moving the later task; its own slot shouldn't block it.
            others = [(p, t) for p, t in plan.scheduled if t is not t2]
            slot = self.find_next_available_slot(t2.duration_minutes, tasks=others)
            lines.append(
                f"    Try moving {t2.title} to {slot}." if slot
                else f"    No free {t2.duration_minutes}-min slot today for {t2.title}."
            )
        return "\n".join(lines)
