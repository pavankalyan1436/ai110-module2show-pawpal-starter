# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

1. Add a pet (name, species, breed, age) to their owner profile.
2. Add or edit a care task for a pet — e.g., schedule a 30-minute walk at 08:00 with high priority that repeats daily.
3. Generate and view today's plan: a sorted list of tasks that fits the owner's available time, with conflict warnings and a short explanation of why tasks were chosen.

**a. Initial design**

My UML has four classes:

- **Task** (dataclass) — one care activity. Holds title, category, duration, priority, optional start time, frequency (once/daily/weekly), due date, and completion status. Responsible for marking itself complete, converting priority into a sortable rank, and producing its next occurrence if it recurs.
- **Pet** (dataclass) — holds basic pet info and owns a list of Tasks. Responsible for adding/removing tasks and returning pending ones.
- **Owner** (dataclass) — holds the owner's name, daily time budget (`available_minutes`), preferences, and a list of Pets. Responsible for managing pets and collecting all tasks across them.
- **Scheduler** — the "brain." Takes an Owner and a day, and is responsible for sorting (by priority and by time), filtering (by pet or status), detecting time conflicts, generating the daily plan within the time budget, and explaining the plan.

Relationships: an Owner has many Pets, a Pet has many Tasks, and a Scheduler plans for one Owner. Keeping scheduling logic in Scheduler (rather than in Owner or Pet) keeps the data classes simple and makes the algorithm easy to test on its own.

**b. Design changes**

<!-- TODO: replace this with what YOUR AI review suggested -->

After an AI review of the skeleton, I changed the Scheduler's methods to work with `(Pet, Task)` pairs instead of bare `Task` objects. A Task doesn't store which pet it belongs to, so a plan of bare Tasks couldn't show "Walk — Biscuit" or filter by pet. Returning pairs solved that without adding a back-reference from Task to Pet (which would create a circular dependency).

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

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

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