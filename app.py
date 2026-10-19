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
                when = f"at {task.time}" if task.time else "with no start time"
                st.success(f"Added '{task.title}' for {pets_by_id[pet_id].name} {when}.")
else:
    st.info("Add a pet before adding tasks.")

all_tasks = owner.get_all_tasks()
if all_tasks:
    st.table(
        [
            {
                "Pet": pet.name,
                "Task": task.title,
                "Time": task.time or "-",
                "Duration (min)": task.duration_minutes,
                "Priority": task.priority,
                "Frequency": task.frequency,
                "Done": task.completed,
            }
            for pet, task in all_tasks
        ]
    )
elif owner.pets:
    st.info("No tasks yet. Add one above.")

st.divider()

# --- Schedule ----------------------------------------------------------------

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    st.markdown(
        f"**Plan for {scheduler.day.isoformat()}:** "
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
                for pet, task in plan.scheduled
            ]
        )
    else:
        st.info("Nothing scheduled for today.")

    if plan.skipped:
        st.markdown("**Skipped**")
        st.table(
            [
                {"Pet": pet.name, "Task": task.title, "Priority": task.priority, "Reason": reason}
                for pet, task, reason in plan.skipped
            ]
        )

    for conflict in scheduler.detect_conflicts(plan.scheduled):
        st.warning(conflict)
