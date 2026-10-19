"""Demo script: build a sample owner, pets, and tasks, then print today's plan."""

from datetime import datetime
from typing import Optional

from pawpal_system import Owner, Pet, Plan, Scheduler, Task


def format_time(hhmm: Optional[str]) -> str:
    """Turn "HH:MM" into "7:30 AM"; untimed tasks show as "Anytime"."""
    if hhmm is None:
        return "Anytime"
    return datetime.strptime(hhmm, "%H:%M").strftime("%I:%M %p").lstrip("0")


def format_priority(priority: str) -> str:
    return priority.capitalize()


def print_schedule(plan: Plan, scheduler: Scheduler) -> None:
    columns = [("Time", 9), ("Pet", 8), ("Task", 22), ("Duration", 9), ("Priority", 8)]
    header = "  ".join(name.ljust(width) for name, width in columns)
    rule = "-" * len(header)

    title = f"Today's Schedule ({scheduler.day.strftime('%A, %B %d, %Y')})"
    print(title)
    print("=" * len(title))
    print(header)
    print(rule)
    for pet, task in plan.scheduled:
        cells = [
            format_time(task.time),
            pet.name,
            task.title + (" (daily)" if task.frequency == "daily" else ""),
            f"{task.duration_minutes} min",
            format_priority(task.priority),
        ]
        print("  ".join(cell.ljust(width) for cell, (_, width) in zip(cells, columns)).rstrip())
    print(rule)
    print(f"Total: {plan.minutes_used} of {scheduler.owner.available_minutes} min")


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90)
    biscuit = Pet(name="Biscuit", species="dog", breed="Golden Retriever", age=4)
    luna = Pet(name="Luna", species="cat", breed="Tabby", age=2)
    owner.add_pet(biscuit)
    owner.add_pet(luna)

    biscuit.add_task(Task("Morning walk", 30, "high", "walk", time="07:30", frequency="daily"))
    biscuit.add_task(Task("Breakfast", 10, "high", "feeding", time="08:00"))
    luna.add_task(Task("Breakfast", 5, "high", "feeding", time="08:15"))
    luna.add_task(Task("Thyroid meds", 5, "high", "meds", time="09:00"))
    luna.add_task(Task("Clean litter box", 15, "medium", "grooming", time="18:00"))
    biscuit.add_task(Task("Fetch session", 20, "medium", "enrichment"))
    biscuit.add_task(Task("Full grooming", 60, "low", "grooming", time="14:00"))  # won't fit

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    print_schedule(plan, scheduler)
    print()
    print(scheduler.explain_plan(plan))


if __name__ == "__main__":
    main()
