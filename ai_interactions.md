# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**Agent used:** Claude Code (Opus 5.5) in VS Code, in agent mode, so it could read files, edit them, and run commands such as `pytest`, `main.py`, and a headless Streamlit test.

**Files modified**

| File | What changed |
|------|--------------|
| `pawpal_system.py` | Duration validation; `detect_conflicts` skips completed tasks and other days, with a `same_day` option; new `conflicting_pairs()` and `find_next_available_slot()`; `explain_plan` suggests a new time for each conflict. |
| `tests/test_pawpal.py` | Grew from 14 to 52 tests. |
| `app.py` | Plan kept in session state, summary line, skipped expander, conflict warnings with a suggested time, pet and "Hide completed" filters. |
| `main.py` | Prints the next available slot for 30-, 60-, and 600-minute tasks. |
| `diagrams/uml.mmd`, `diagrams/uml_final.mmd` | Notes and new methods on the original diagram; a new final diagram that matches the code. |
| `README.md` | Features, Demo Walkthrough, Priority-Based Scheduling, and UML sections; restored the Testing and Smarter Scheduling sections. |

**What task did you give the agent?**

I gave it a series of tasks, one at a time, each reviewed before the next:

1. Compare my tests against the important edge cases for a scheduler with sorting and recurring tasks, and list what's missing.
2. Fix the bugs it found, add the missing tests, and pass `due_date` explicitly so the tests don't depend on today's date.
3. Make overdue tasks in the plan count as today when checking for conflicts.
4. Polish `app.py` to show off the scheduler: a saved plan, a summary line, skipped reasons, conflict tips, and filters.
5. Add a test for `conflicting_pairs()` and bring the UML up to date in a new `uml_final.mmd`.
6. Update the README, using real output rather than made-up examples.
7. Add `find_next_available_slot()`, use it to suggest new times for conflicts, test it, and show it in `main.py`.

I always said "don't commit" so I could review the diff myself.

**What did the agent do?**

- **Found real bugs before writing tests.** It read `pawpal_system.py` and ran small scripts to check suspicions. That showed a negative duration let an 80-minute task fit into a 30-minute budget, and that a completed daily walk "conflicted" with tomorrow's copy.
- **Fixed and tested in small steps.** After each change it ran `.venv/bin/python -m pytest` (14 → 44 → 45 → 46 → 52 tests) and re-ran `main.py` to make sure the demo still worked.
- **Tested the Streamlit app without a browser** using Streamlit's `AppTest`. It clicked "Generate schedule", changed the filters, and checked the warnings, summary, and skipped list.
- **Rendered the UML to an image** with the Mermaid command-line tool and looked at it, rather than assuming the syntax was right.
- **Noticed problems outside the task and asked before fixing them.** It found that an earlier commit had truncated `README.md` and deleted three sections, and restored them from git history. It also pointed out that `main.py` checks conflicts differently from the plan, and that `reflection.md` still says 45 tests.

**What did you have to verify or fix manually?**

- **Scope decisions:** I chose which suggestions to act on. I asked for the same-day conflict fix but **not** the midnight-crossing fix; that's tested as a known limitation instead. I kept the original `uml.mmd` and had the final diagram saved as a new file.
- **A side effect of the agent's own fix:** after the same-day conflict fix, it pointed out that an overdue 08:00 task would no longer be flagged against today's 08:00 task. I asked for the `same_day` option to close that gap.
- **The agent's own mistakes, caught by its checks:** its first app test changed the wrong dropdown, so the filter looked broken until it targeted the dropdown by label. The first UML notes showed a literal `\n` until it rendered the image and switched to `<br>`.
- **Something to watch:** each conflict's suggested time is worked out on its own, so two conflicts can get the same suggestion. One of the tests shows Walk and Ear drops both told to move to 08:00. It's still a useful hint, but the owner should check that the new times don't clash with each other.
- **What I checked myself:** I read each diff, ran `main.py`, and opened the app in the browser before committing.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | | |
| **Prompt** | | |
| **Response summary** | | |
| **What was useful** | | |
| **Problems noticed** | | |
| **Decision** | | |

**Which approach did you use in your final implementation and why?**

<!-- Your conclusion -->
