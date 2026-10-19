# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

1. Add a pet (name, species, breed, age) to their owner profile.
2. Add or edit a care task for a pet — e.g., schedule a 30-minute walk at 08:00 with high priority that repeats daily.
3. Generate and view today's plan: a sorted list of tasks that fits the owner's available time, with conflict warnings and a short explanation of why tasks were chosen.

**a. Initial design**

My UML has five classes:

- **Task** (dataclass) — one care activity. Holds a unique id, title, category, duration, priority, optional start time, frequency (once/daily/weekly), due date, and completion status. Responsible for validating its own values, marking itself complete, converting priority into a sortable rank, and producing its next occurrence if it recurs.
- **Pet** (dataclass) — holds a unique id, basic pet info, and a list of Tasks. Responsible for adding, removing, finding, and completing tasks (including adding the next occurrence of recurring tasks).
- **Owner** (dataclass) — holds the owner's name, daily time budget (`available_minutes`), and a list of Pets. Responsible for managing pets and collecting all tasks across them.
- **Plan** (dataclass) — the result of scheduling: which tasks were scheduled, which were skipped (with a reason), and total minutes used.
- **Scheduler** — the "brain." Takes an Owner and a day, and is responsible for sorting (by priority and by time), filtering, detecting time conflicts, generating a Plan within the time budget, and explaining it.

Relationships: an Owner has many Pets, a Pet has many Tasks, a Scheduler plans for one Owner and produces a Plan. Keeping scheduling logic in Scheduler (rather than in Owner or Pet) keeps the data classes simple and makes the algorithm easy to test on its own.

**b. Design changes**

After asking AI to review my skeleton, I made five changes:

- **Added `Pet.complete_task()`** — `next_occurrence()` created the next recurring task, but nothing saved it to the pet, so daily/weekly tasks would never actually repeat. It's also safe to call twice so a double-click doesn't create duplicates.
- **Added unique `id`s to Task and Pet** — looking things up by name breaks when there are two "Walk" tasks or two pets named "Max."
- **Added a `Plan` dataclass** — so the scheduler can explain which tasks were skipped and why, not just which were chosen.
- **Removed `Owner.preferences`** — no method used it, so it was a promise the design didn't keep.
- **Added validation in `Task.__post_init__`** — a typo like `"High"` or a time like `"9:00"` would have silently sorted wrong.

I deferred the AI's suggestions about overlap detection, sort tie-breakers, and `filter_tasks` to the algorithm phase. In Phase 4 I implemented them, adding `Task.overlaps()`, `Scheduler.mark_task_complete()`, and a `due_by` filter. In Phase 6 I added `Scheduler.conflicting_pairs()` so the UI could show a helpful tip for each conflict without parsing warning strings. The final diagram is in `diagrams/uml_final.mmd`.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers four constraints: (1) the owner's daily time budget (`available_minutes`), (2) task priority (high → medium → low), (3) due date — only tasks due today or overdue are planned, and (4) start time, used for ordering and conflict detection. I ranked priority first because missing meds or a feeding is worse than missing grooming. The time budget comes next so the plan is realistic.

**b. Tradeoffs**

The scheduler picks tasks greedily — highest priority first, shorter first on ties — and skips anything that doesn't fit. This can leave time unused or skip a task that a smarter "knapsack" algorithm would fit in. I accepted this because a predictable rule ("important things first") is easier for a pet owner to understand and trust.

A second tradeoff: conflicts are reported as warnings, not prevented. In my demo, the 07:30 walk overlaps the 07:45 ear drops, and both are still scheduled with a warning. Automatically moving tasks would be more complex and might move something the owner deliberately timed (like meds), so I let the owner decide.

When I asked AI to simplify `detect_conflicts`, it suggested replacing my "sweep" loop with a simple pairwise check using a new `Task.overlaps()` method. The sweep is technically faster when there are few overlaps, but a pet owner's day has maybe 5–20 timed tasks, so the speed difference is unnoticeable. I chose the simpler version because the overlap rule (`a.start < b.end and b.start < a.end`) is readable in one line, and `Task.overlaps()` can be tested on its own. My existing tests (back-to-back, nested, untimed) passed unchanged, which confirmed the rewrite didn't change behavior.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI at every stage: brainstorming the UML, generating class skeletons, reviewing the design, implementing methods, writing the `main.py` demo, connecting the Streamlit UI, suggesting algorithm improvements, and drafting tests.

The most effective features were **agent mode** (the AI could edit `pawpal_system.py`, `main.py`, `app.py`, and the tests together, then run them to check its own work) and **attaching specific files** so its suggestions were based on my real code. The most helpful prompts listed exact requirements — for example, "Scheduler must only read from `owner.get_all_tasks()`" and "skip tasks that don't fit, don't break." Vague prompts got vague results; precise prompts got code I could actually check.

Using **separate chat sessions** for each phase (design, algorithms, testing) kept each conversation focused. The algorithm chat didn't get distracted by old UI discussions, and the testing chat reviewed the code with fresh eyes, which is how it found the negative-duration bug the earlier sessions missed.

**b. Judgment and verification**

I didn't accept AI suggestions wholesale. The design review gave 12 suggestions and I applied five at first, deferring the rest. In Phase 4 the AI suggested 13 algorithm improvements; I picked seven (overlap detection, time-in-minutes, recurrence based on today, sort tie-breakers, filtering by pet id and due date) and skipped the rest — like labeling same-pet vs. cross-pet conflicts and duplicate detection — because they added complexity the app didn't need yet. The AI also caught one of my mistakes: I had renamed the diagram to `uml_draft.mmd`, but the starter repo expected `uml.mmd`.

Testing in the browser caught a bug the AI's automated checks missed: my start times weren't being saved. The empty time box showed `08:00` as grey placeholder text, which looked like a real value. Switching to a time picker fixed it.

I verified the AI's work by running `main.py` and checking the output by hand (scheduled tasks add up to exactly 90 of 90 minutes, the 60-minute grooming was correctly skipped, and the completed daily walk reappeared due tomorrow), by testing the app in the browser, and by running `pytest` (52 passed).

---

## 4. Testing and Verification

**a. What you tested**

My 52 tests cover sorting (chronological order, untimed last, priority tie-breaks), filtering (by pet, status, and due date), recurrence (daily → tomorrow, weekly → +7 days, one-time tasks don't repeat, no duplicates on double-complete, Dec 31 → Jan 1 rollover), conflict detection (same start time, overlapping durations, three-way overlaps, back-to-back is not a conflict), `generate_plan` (exact fit, skip-and-continue, overdue included, future and completed excluded, empty inputs), and input validation. These matter because they're what a pet owner relies on — a missed recurring medication or a hidden conflict would be a real problem.

Testing found real bugs. A negative duration added time back to the budget, so an 80-minute task fit into a 30-minute day; I fixed it by rejecting durations ≤ 0. Also, a completed daily walk was flagged as conflicting with tomorrow's copy; I fixed `detect_conflicts` to skip completed tasks and compare only same-day tasks, and then made sure overdue tasks scheduled today are still checked against today's tasks.

**b. Confidence**

4/5. All 52 tests pass and I checked the demo output by hand. I'm not at 5 because the tests cover the logic layer, not the Streamlit UI — the time-input bug I found in Phase 3 was a UI problem no unit test caught. Next I'd test tasks that cross midnight (a known limitation: a 23:30 task lasting 60 minutes doesn't conflict with a 00:15 task), many tasks at the same time, and Streamlit UI behavior.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the scheduling logic and the test suite. The scheduler handles priorities, a time budget, recurring tasks, and overlap detection, and the tests gave me confidence to refactor — when I swapped `detect_conflicts` for a simpler version, the tests proved nothing broke. I'm also happy that the Streamlit app shows the scheduler's reasoning (skipped tasks with reasons, conflict tips) instead of just a list.

**b. What you would improve**

As extensions, I added `find_next_available_slot()`, which suggests a free time for each conflict (e.g., "Try moving Ear drops to 07:00"), and JSON persistence so pets and tasks survive restarts. One limitation: each slot suggestion is calculated separately, so two conflicting tasks can be told to move to the same slot. Next I'd make the planner overlap-aware so it actually reschedules tasks, handle tasks that cross midnight, and add automated tests for the Streamlit UI.

**c. Key takeaway**

Being the "lead architect" means AI writes code fast, but I decide what gets built. The AI gave me 12 design suggestions and 13 algorithm ideas — accepting all of them would have made the system bloated. My job was choosing what mattered, saying no to the rest, and verifying every change by running the demo, checking the math by hand, and testing in the browser. The bugs I caught — like the time-input placeholder — came from checking the AI's work, not from trusting it.