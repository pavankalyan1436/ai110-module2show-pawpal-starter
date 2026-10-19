# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🧩 Implementation Summary

All backend logic lives in `pawpal_system.py`. The classes work together like this: **Owner → Pets → Tasks**, and the **Scheduler** reads from the Owner to produce a **Plan**.

| Class | What it does |
|-------|--------------|
| `Task` | One care activity (title, duration, priority, optional `HH:MM` time, frequency, due date, completed). Validates its own values, can `mark_complete()`, and creates its `next_occurrence()` for daily/weekly tasks. |
| `Pet` | Stores pet details and its list of tasks. `add_task()`, `remove_task()`, `get_task()`, and `complete_task()`, which marks a task done and adds the next occurrence if it recurs (safe to call twice). |
| `Owner` | Stores the owner's name, daily time budget (`available_minutes`), and pets. `get_all_tasks()` returns every `(pet, task)` pair across all pets. |
| `Plan` | The scheduler's result: `scheduled` tasks, `skipped` tasks with a reason, and `minutes_used`. |
| `Scheduler` | The "brain." Gets tasks only through `owner.get_all_tasks()`, keeps tasks due today (or overdue) that aren't done, picks them by priority until the time budget runs out, orders the result by start time, flags tasks whose time ranges overlap, and explains the plan. |

Run the CLI demo with:

```bash
python main.py
```

## 🖥️ Sample Output

Output of `python main.py`:

```
Today's Schedule (Sunday, October 18, 2026)
===========================================
Time       Pet       Task                    Duration   Priority
----------------------------------------------------------------
7:30 AM    Biscuit   Morning walk (daily)    30 min     High
8:00 AM    Biscuit   Breakfast               10 min     High
8:15 AM    Luna      Breakfast               5 min      High
9:00 AM    Luna      Thyroid meds            5 min      High
6:00 PM    Luna      Clean litter box        15 min     Medium
Anytime    Biscuit   Fetch session           20 min     Medium
----------------------------------------------------------------
Total: 85 of 90 min

Plan for 2026-10-18: 85 of 90 min used
Tasks were picked by