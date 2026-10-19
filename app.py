import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan your pets' care tasks for today based on time and priority.")

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time and priority.
"""
    )

# --- Owner (stored once per browser session) ---------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=90)

owner: Owner = st.session_state.owner

st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name, key="owner_name")
with col2:
    owner.available_minutes = int(
        st.number_input(
            "Available minutes today",
            min_value=0,
            max_value=1440,
            value=owner.available_minutes,
            key="owner_minutes",
            on_change=lambda: st.session_state.pop("plan", None),  # budget changed: plan is stale
        )
    )

if st.button("Reset (clear owner, pets, and tasks)"):
    st.session_state.clear()
    st.rerun()

st.divider()

# --- Pets --------------------------------------------------------------------

st.subheader("Pets")

with st.form("add_pet", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        pet_name = st.text_input("Pet name")
        breed = st.text_input("Breed (optional)")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
        age = st.number_input("Age (years)", min_value=0, max_value=40, value=0)
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("Pet name can't be blank.")
        else:
            owner.add_pet(
                Pet(name=pet_name.strip(), species=species, breed=breed.strip(), age=int(age))
            )
            st.success(f"Added {pet_name.strip()}.")

if owner.pets:
    st.table(
        [
            {"Name": p.name, "Species": p.species, "Breed": p.breed or "-", "Age": p.age}
            for p in owner.pets
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Tasks -------------------------------------------------------------------

st.subheader("Tasks")

if owner.pets:
    pets_by_id = {p.id: p for p in owner.pets}
    with st.form("add_task", clear_on_submit=True):
        pet_id = st.selectbox(
            "Pet",
            list(pets_by_id),
            format_func=lambda pid: f"{pets_by_id[pid].name} ({pets_by_id[pid].species})",
        )
        title = st.text_input("Task title", value="Morning walk")
        col1, col2 = st.columns(2)
        with col1:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            # value=None starts the picker empty, so "no start time" is unambiguous.
            start_time = st.time_input("Start time (optional)", value=None, step=300)
        with col2:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
        if st.form_submit_button("Add task"):
            try:
                if not title.strip():
                    raise ValueError("Task title can't be blank.")
                task = Task(
                    title=title.strip(),
                    duration_minutes=int(duration),
                    priority=priority,
                    time=start_time.strftime("%H:%M") if start_time else None,
                    frequency=frequency,
                )
            except ValueError as e:
                st.error(str(e))
            else:
                pets_by_id[pet_id].add_task(task)
                st.session_state.pop("plan", None)  # new task: plan is stale
                when = f"at {task.time}" if task.time else "with no start time"
                st.success(f"Added '{task.title}' for {pets_by_id[pet_id].name} {when}.")
else:
    st.info("Add a pet before adding tasks.")

scheduler = Scheduler(owner)
all_tasks = scheduler.sort_by_time(owner.get_all_tasks())
if all_tasks:
    col1, col2 = st.columns([2, 1])
    with col1:
        pet_filter = st.selectbox(
            "Show tasks for",
            ["All"] + [p.id for p in owner.pets],
            format_func=lambda pid: pid if pid == "All" else owner.get_pet(pid).name,
        )
    with col2:
        st.write("")  # nudge the checkbox down to line up with the dropdown
        hide_completed = st.checkbox("Hide completed")

    shown = scheduler.sort_by_time(
        scheduler.filter_tasks(
            pet_id=None if pet_filter == "All" else pet_filter,
            completed=False if hide_completed else None,
        )
    )
    if shown:
        st.table(
            [
                {
                    "Pet": pet.name,
                    "Task": task.title,
                    "Time": task.time or "-",
                    "Duration (min)": task.duration_minutes,
                    "Priority": task.priority,
                    "Frequency": task.frequency,
                    "Due": task.due_date.isoformat(),
                    "Done": "✅" if task.completed else "",
                }
                for pet, task in shown
            ]
        )
    else:
        st.info("No tasks match these filters.")

    # A message set before st.rerun() would be lost, so it's shown on the next run.
    if "done_message" in st.session_state:
        st.success(st.session_state.pop("done_message"))

    pending = {task.id: (pet, task) for pet, task in all_tasks if not task.completed}
    if pending:
        with st.form("mark_done"):
            done_id = st.selectbox(
                "Mark a task done",
                list(pending),
                format_func=lambda tid: (
                    f"{pending[tid][1].title} ({pending[tid][0].name}) - "
                    f"{pending[tid][1].time or 'anytime'}, due {pending[tid][1].due_date.isoformat()}"
                ),
            )
            if st.form_submit_button("Mark done"):
                pet, task = pending[done_id]
                next_task = scheduler.mark_task_complete(pet.id, task.id)
                st.session_state.pop("plan", None)  # task finished: plan is stale
                message = f"Marked '{task.title}' for {pet.name} done."
                if next_task is not None:
                    message += f" Next one is due {next_task.due_date.isoformat()}."
                st.session_state.done_message = message
                st.rerun()
elif owner.pets:
    st.info("No tasks yet. Add one above.")

st.divider()

# --- Schedule ----------------------------------------------------------------

st.subheader("Build Schedule")

# The plan lives in session state so it survives reruns from other clicks.
# Adding a task, marking one done, or changing the time budget clears it.
if st.button("Generate schedule"):
    st.session_state.plan = scheduler.generate_plan()

plan = st.session_state.get("plan")
if plan is not None:
    count = len(plan.scheduled)
    st.success(
        f"{count} task{'s' if count != 1 else ''} scheduled · "
        f"{plan.minutes_used} of {owner.available_minutes} min used"
    )

    if plan.scheduled:
        st.table(
            [
                {
                    "Time": task.time or "Anytime",
                    "Pet": pet.name,
                    "Task": task.title,
                    "Duration (min)": task.duration_minutes,
                    "Priority": task.priority,
                }
                for pet, task in scheduler.sort_by_time(plan.scheduled)
            ]
        )
    else:
        st.info("Nothing scheduled for today.")

    if plan.skipped:
        with st.expander(f"Skipped ({len(plan.skipped)})"):
            for pet, task, reason in plan.skipped:
                st.info(f"**{task.title}** ({pet.name}, {task.priority}): {reason}")

    for (p1, t1), (p2, t2) in scheduler.conflicting_pairs(plan.scheduled, same_day=True):
        st.warning(
            f"⚠️ {t1.title} ({p1.name}) overlaps {t2.title} ({p2.name}) at {t2.time}. "
            "Consider moving one."
        )
