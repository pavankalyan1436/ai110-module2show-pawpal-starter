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

I chose not to apply the AI's suggestions about overlap detection, plan ordering, and `filter_tasks` yet, because those belong to the algorithm phase.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

I used AI at every stage: brainstorming the UML, generating class skeletons, reviewing the design for missing relationships, implementing the methods, writing the `main.py` demo, and drafting tests. The most helpful prompts were specific ones that listed exact requirements — for example, "Scheduler must only read from `owner.get_all_tasks()`" and "skip tasks that don't fit, don't break." Vague prompts got vague results; precise prompts got code I could actually check.

**b. Judgment and verification**

The AI's design review gave 12 suggestions, and I didn't accept all of them. I applied five (ids, `complete_task`, `Plan`, validation, removing the unused `preferences`) and deferred overlap detection, plan ordering, and `filter_tasks` changes to the algorithm phase to keep the skeleton focused. The AI also went slightly beyond what I asked — it wrote real validation code instead of a stub — and I kept that after confirming it rejected bad inputs like `"High"` and `"9:00"`. It also caught a mistake: I had renamed the diagram to `uml_draft.mmd`, but the starter repo expected `uml.mmd`, so I renamed it back.

I verified the AI's code by running `main.py` and checking the math by hand (scheduled tasks add up to 85 of 90 minutes, so the 60-minute grooming was correctly skipped), and by running `pytest` (2 passed).

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?