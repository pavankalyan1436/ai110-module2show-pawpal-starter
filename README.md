# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## ✨ Features

| Feature | What it does | Method(s) |
|---------|--------------|-----------|
| **Sorting by time** | Lists tasks by start time, untimed tasks last; ties go high → low priority, then shorter first. | `Scheduler.sort_by_time()` (`sort_by_priority()` for the planning order) |
| **Filtering** | Shows tasks for one pet (by id or case-insensitive name), by completion status, and/or due on or before a date. | `Scheduler.filter_tasks()` |
| **Daily / weekly recurrence** | Completing a recurring task adds its next occurrence, 1 or 7 days after the due date or the completion day, whichever is later. Completing twice does nothing. | `Scheduler.mark_task_complete()` → `Pet.complete_task()` → `Task.next_occurrence()` |
| **Overlap conflict warnings** | Flags every pair of timed tasks whose time ranges overlap (back-to-back is fine). Completed and untimed tasks are ignored; `same_day=True` treats the whole plan as today so overdue tasks are checked too. | `Task.overlaps()`, `Scheduler.conflicting_pairs()`, `Scheduler.detect_conflicts()` |
| **Next available slot** | Finds the earliest `HH:MM` (07:00–21:00 by default) where a task of a given length fits without overlapping today's timed tasks, or `None` if there's no room. Used to suggest a new time for each conflict, e.g. "Try moving Ear drops to 07:00." | `Scheduler.find_next_available_slot()` |
| **Time-budget planning with skip reasons** | Picks today's and overdue tasks by priority until `available_minutes` runs out, skips what doesn't fit with a reason, and keeps trying smaller tasks. | `Scheduler.generate_plan()` → `Plan`, `Scheduler.explain_plan()` |
| **Input validation** | Rejects non-positive durations, unknown priorities/frequencies, and times that aren't zero-padded `HH:MM`. | `Task.__post_init__()` |

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

## 📸 Demo Walkthrough

Start the app with `streamlit run app.py`.

### Main UI features

- **Owner:** set the owner's name and how many minutes they have today. A reset button clears everything.
- **Pets:** add a pet (name, species, breed, age); all pets are listed in a table.
- **Tasks:** add a task for a pet with a title, duration, optional start time, priority, and frequency (once, daily, weekly). Invalid input shows an error instead of crashing.
- **Task list:** a table sorted by time, with a **Show tasks for** dropdown ("All" or one pet) and a **Hide completed** checkbox.
- **Mark done:** pick a pending task and mark it done. For a recurring task, the app says when the next one is due.
- **Build Schedule:** generates today's plan and keeps it on screen while you use the rest of the page. Adding a task, marking one done, or changing the time budget clears it so you never see an out-of-date plan.

### Example workflow

1. **Add the owner.** Enter "Jordan" and set available minutes to 90.
2. **Add pets.** Add Biscuit (dog, Golden Retriever, 4) and Luna (cat).
3. **Add tasks.** For Biscuit: "Morning walk", 30 min, 07:30, high, daily. For Luna: "Ear drops", 5 min, 07:45, high. Add a few more, including a long low-priority task such as a 60-minute grooming.
4. **Generate the schedule.** Click **Generate schedule**. A green summary appears, e.g. "7 tasks scheduled · 90 of 90 min used", followed by the schedule table.
5. **Mark a task done.** Mark Biscuit's "Morning walk" done. The app confirms it and says the next walk is due tomorrow.
6. **See the recurrence.** The task list now shows the completed walk and a new walk due tomorrow. Tick **Hide completed** to see only what's left, and pick a pet in the dropdown to narrow the list.

### Scheduler behaviors you'll see

- **Sorting:** the schedule is chosen by priority but shown by start time, with untimed tasks at the bottom as "Anytime".
- **Skipped tasks:** tasks that don't fit the time budget are listed under a **Skipped** expander with the reason, e.g. "not enough time (needs 60 min, 0 min left)".
- **Conflict warnings:** each overlap gets its own warning, e.g. "⚠️ Morning walk (Biscuit) overlaps Ear drops (Luna) at 07:45. Try moving Ear drops to 07:00." The suggested time is the earliest free slot that fits the task.

### CLI demo

`python main.py` runs the same scenario in the terminal: it lists the tasks as added, sorted by time, and filtered to one pet, then prints the schedule, the plan explanation (with a suggested time for each conflict), conflicts, the next free slot for a few task lengths, and a recurring task being completed. Example output (dates depend on the day you run it):

```
All tasks (as added)
--------------------
  Anytime   Biscuit  Fetch session      due 2026-10-19  [todo]
  8:00 AM   Biscuit  Breakfast          due 2026-10-19  [todo]
  7:30 AM   Biscuit  Morning walk       due 2026-10-19  [todo]
  2:00 PM   Biscuit  Full grooming      due 2026-10-19  [todo]
  6:00 PM   Luna     Clean litter box   due 2026-10-19  [todo]
  9:00 AM   Luna     Thyroid meds       due 2026-10-19  [todo]
  8:15 AM   Luna     Breakfast          due 2026-10-19  [todo]
  7:45 AM   Luna     Ear drops          due 2026-10-19  [todo]

All tasks (sorted by time)
--------------------------
  7:30 AM   Biscuit  Morning walk       due 2026-10-19  [todo]
  7:45 AM   Luna     Ear drops          due 2026-10-19  [todo]
  8:00 AM   Biscuit  Breakfast          due 2026-10-19  [todo]
  8:15 AM   Luna     Breakfast          due 2026-10-19  [todo]
  9:00 AM   Luna     Thyroid meds       due 2026-10-19  [todo]
  2:00 PM   Biscuit  Full grooming      due 2026-10-19  [todo]
  6:00 PM   Luna     Clean litter box   due 2026-10-19  [todo]
  Anytime   Biscuit  Fetch session      due 2026-10-19  [todo]

Luna's tasks only
-----------------
  7:45 AM   Luna     Ear drops          due 2026-10-19  [todo]
  8:15 AM   Luna     Breakfast          due 2026-10-19  [todo]
  9:00 AM   Luna     Thyroid meds       due 2026-10-19  [todo]
  6:00 PM   Luna     Clean litter box   due 2026-10-19  [todo]

Today's Schedule (Monday, October 19, 2026)
===========================================
Time       Pet       Task                    Duration   Priority
----------------------------------------------------------------
7:30 AM    Biscuit   Morning walk (daily)    30 min     High
7:45 AM    Luna      Ear drops               5 min      High
8:00 AM    Biscuit   Breakfast               10 min     High
8:15 AM    Luna      Breakfast               5 min      High
9:00 AM    Luna      Thyroid meds            5 min      High
6:00 PM    Luna      Clean litter box        15 min     Medium
Anytime    Biscuit   Fetch session           20 min     Medium
----------------------------------------------------------------
Total: 90 of 90 min

Plan for 2026-10-19: 90 of 90 min used
Tasks were picked by priority (high first, shorter first on ties), then listed by start time (untimed last).

Scheduled:
  07:30  Morning walk (Biscuit) - 30 min [high]
  07:45  Ear drops (Luna) - 5 min [high]
  08:00  Breakfast (Biscuit) - 10 min [high]
  08:15  Breakfast (Luna) - 5 min [high]
  09:00  Thyroid meds (Luna) - 5 min [high]
  18:00  Clean litter box (Luna) - 15 min [medium]
  --:--  Fetch session (Biscuit) - 20 min [medium]

Skipped:
  Full grooming (Biscuit) [low]: not enough time (needs 60 min, 0 min left)

Warnings:
  Conflict: Morning walk (Biscuit, 07:30-08:00) overlaps Ear drops (Luna, 07:45-07:50)
    Try moving Ear drops to 07:00.

Conflict check (today's incomplete tasks)
-----------------------------------------
  Conflict: Morning walk (Biscuit, 07:30-08:00) overlaps Ear drops (Luna, 07:45-07:50)

Next available slot in today's plan (07:00-21:00)
-------------------------------------------------
   30-min task: 7:00 AM
   60-min task: 9:05 AM
  600-min task: no room today

Completed 'Morning walk' for Biscuit.
Next 'Morning walk' is due 2026-10-20.

Incomplete tasks
----------------
  7:30 AM   Biscuit  Morning walk       due 2026-10-20  [todo]
  7:45 AM   Luna     Ear drops          due 2026-10-19  [todo]
  8:00 AM   Biscuit  Breakfast          due 2026-10-19  [todo]
  8:15 AM   Luna     Breakfast          due 2026-10-19  [todo]
  9:00 AM   Luna     Thyroid meds       due 2026-10-19  [todo]
  2:00 PM   Biscuit  Full grooming      due 2026-10-19  [todo]
  6:00 PM   Luna     Clean litter box   due 2026-10-19  [todo]
  Anytime   Biscuit  Fetch session      due 2026-10-19  [todo]
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage (needs `pip install pytest-cov`):
pytest --cov
```

The 56 tests in `tests/test_pawpal.py` cover sorting (time order, tie-breaks), filtering, plan generation (exact fit, skip-and-continue, overdue/future/completed tasks, empty inputs, zero budget), recurrence (daily, weekly, one-off, completing twice, early and late completion, month/year rollover), conflict detection (overlaps, back-to-back, same start time, three-way, other days, `same_day`), finding the next available slot (empty day, gaps between tasks, exact fit at day end, no room left, ignored tasks, suggestions in the plan explanation), JSON persistence (round-trip, missing file, recurrence after loading, invalid data), and input validation. Scheduling tests use fixed dates so they don't depend on when they run.

Sample test output:

```
tests/test_pawpal.py ................................................... [ 91%]
.....                                                                    [100%]

============================== 56 passed in 0.03s ==============================
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_priority()`, `Scheduler.sort_by_time()` | Planning picks by priority (shorter first on ties); the plan is shown by start time, untimed last. |
| Filtering | `Scheduler.filter_tasks()`, `Scheduler.generate_plan()` | Filter by pet, completion, or due date. Planning skips tasks that don't fit the remaining time and keeps trying smaller ones. |
| Conflict handling | `Task.overlaps()`, `Scheduler.conflicting_pairs()`, `Scheduler.detect_conflicts()` | Overlapping time ranges are warned about, not blocked. Back-to-back tasks are fine. Known limitation: tasks running past midnight aren't checked. |
| Recurring tasks | `Task.next_occurrence()`, `Pet.complete_task()`, `Scheduler.mark_task_complete()` | Daily = +1 day, weekly = +7 days, counted from the later of the due date and the completion day. |

## ⭐ Priority-Based Scheduling

`Scheduler.generate_plan()` builds the day's plan in two steps:

1. **Pick by priority.** It takes every incomplete task due today or earlier and sorts them high → medium → low, with shorter tasks first when priorities tie (`sort_by_priority()`). It then goes down that list and adds each task that still fits in the owner's `available_minutes`. A task that doesn't fit is skipped with a reason, and the scheduler keeps going in case a smaller task still fits.
2. **List by time.** The chosen tasks are re-sorted by start time (`sort_by_time()`), with untimed tasks last, so the plan reads like a day.

Priority decides *what* makes the cut and time decides *the order you see*. In the `python main.py` demo (90-minute budget), the five high-priority tasks take 55 minutes and the two medium ones take the remaining 35. The low-priority 60-minute grooming is skipped, even though its 2:00 PM start comes before the 6:00 PM litter box:

```
Scheduled:
  07:30  Morning walk (Biscuit) - 30 min [high]
  07:45  Ear drops (Luna) - 5 min [high]
  08:00  Breakfast (Biscuit) - 10 min [high]
  08:15  Breakfast (Luna) - 5 min [high]
  09:00  Thyroid meds (Luna) - 5 min [high]
  18:00  Clean litter box (Luna) - 15 min [medium]
  --:--  Fetch session (Biscuit) - 20 min [medium]

Skipped:
  Full grooming (Biscuit) [low]: not enough time (needs 60 min, 0 min left)
```

## 💾 Data Persistence

The Streamlit app saves everything to `data.json` (next to `app.py`), so your owner, pets, and tasks survive a browser refresh or an app restart.

**How it works**

1. **Load on startup.** When a new browser session starts, the app calls `Owner.load_from_json("data.json")`. If the file doesn't exist it returns `None`, and the app starts with a default owner. If the file can't be read, the app shows a warning and starts fresh.
2. **Save after each change.** Adding a pet, adding a task, marking a task done, and changing the owner's name or available minutes each call `owner.save_to_json("data.json")`. Generating a schedule or changing the filters doesn't save, because those don't change your data.
3. **Reset clears it.** The **Reset** button deletes `data.json` and clears the session, so the next run starts from scratch.

**What's stored:** the owner's name and available minutes, and every pet and task with its `id`, due date as an ISO string (e.g. `"2026-10-19"`), and completed status. Keeping ids means recurring tasks and "Mark done" still work after loading. Loaded tasks go through the same validation as new ones, so a hand-edited file with a bad priority or time is rejected instead of quietly causing wrong results.

**Methods:** `Task.to_dict()` / `Task.from_dict()`, `Pet.to_dict()` / `Pet.from_dict()`, and `Owner.to_dict()` / `Owner.from_dict()` convert to and from plain dicts. `Owner.save_to_json(path)` writes the file (to a temporary file first, then swapped in, so a crash can't leave a half-written file), and `Owner.load_from_json(path)` is a classmethod that reads it back. Only the standard library (`json`) is used.

**Files modified**

| File | Change |
|------|--------|
| `pawpal_system.py` | `to_dict()` / `from_dict()` on `Task`, `Pet`, and `Owner`; `Owner.save_to_json()` and `Owner.load_from_json()`. |
| `app.py` | Loads `data.json` when the session starts, saves after every change, and Reset deletes the file. |
| `tests/test_pawpal.py` | Round-trip (pets, tasks, ids, dates, completed status), missing file returns `None`, a recurring task still recurs after loading, and invalid saved data is rejected. Tests use pytest's `tmp_path`, so they never touch the real `data.json`. |
| `.gitignore` | Ignores `data.json` (and its temporary file) so personal data isn't committed. |
| `diagrams/uml_final.mmd` | Adds the new methods. |

## 📐 UML

The final class diagram is in [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd). It shows the five classes (`Owner`, `Pet`, `Task`, `Plan`, `Scheduler`), how they call each other (for example `Scheduler.mark_task_complete()` → `Pet.complete_task()` → `Task.next_occurrence()`, and `Scheduler.conflicting_pairs()` → `Task.overlaps()`), and notes on validation, the `same_day` rule, and the midnight limitation. GitHub renders `.mmd` files as text; paste the file into [mermaid.live](https://mermaid.live) to view it as a diagram. The original design is kept in [`diagrams/uml.mmd`](diagrams/uml.mmd).
