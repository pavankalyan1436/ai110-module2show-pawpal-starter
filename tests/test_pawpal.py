from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_sets_completed_true():
    task = Task("Morning walk", 30)
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Biscuit", "dog")
    before = len(pet.tasks)

    pet.add_task(Task("Breakfast", 10))

    assert len(pet.tasks) == before + 1


# --- Helpers -----------------------------------------------------------------

def make_owner(*pets):
    owner = Owner("Jordan", available_minutes=120)
    for pet in pets:
        owner.add_pet(pet)
    return owner


def titles(pairs):
    return [task.title for _, task in pairs]


# --- Sorting -----------------------------------------------------------------

def test_sort_by_time_orders_chronologically_with_untimed_last():
    pet = Pet("Biscuit", "dog")
    pet.add_task(Task("Anytime play", 10))
    pet.add_task(Task("Dinner", 10, time="18:00"))
    pet.add_task(Task("Walk", 30, time="07:30"))
    pet.add_task(Task("Meds", 5, time="09:00"))
    scheduler = Scheduler(make_owner(pet))

    result = scheduler.sort_by_time(scheduler.owner.get_all_tasks())

    assert titles(result) == ["Walk", "Meds", "Dinner", "Anytime play"]


def test_sort_by_time_breaks_ties_by_priority_then_duration():
    pet = Pet("Biscuit", "dog")
    pet.add_task(Task("Low", 5, "low", time="08:00"))
    pet.add_task(Task("High long", 20, "high", time="08:00"))
    pet.add_task(Task("High short", 5, "high", time="08:00"))
    pet.add_task(Task("Untimed low", 5, "low"))
    pet.add_task(Task("Untimed high", 5, "high"))
    scheduler = Scheduler(make_owner(pet))

    result = scheduler.sort_by_time(scheduler.owner.get_all_tasks())

    assert titles(result) == ["High short", "High long", "Low", "Untimed high", "Untimed low"]


# --- Filtering ---------------------------------------------------------------

def test_filter_by_pet_returns_only_that_pets_tasks():
    biscuit = Pet("Biscuit", "dog")
    luna = Pet("Luna", "cat")
    biscuit.add_task(Task("Walk", 30))
    luna.add_task(Task("Meds", 5))
    luna.add_task(Task("Litter", 15))
    scheduler = Scheduler(make_owner(biscuit, luna))

    by_name = scheduler.filter_tasks(pet_name="LUNA")  # case-insensitive
    by_id = scheduler.filter_tasks(pet_id=luna.id)

    assert sorted(titles(by_name)) == ["Litter", "Meds"]
    assert by_id == by_name
    assert all(pet is luna for pet, _ in by_id)


def test_filter_due_by_hides_future_occurrences():
    today = date(2026, 10, 19)
    pet = Pet("Biscuit", "dog")
    walk = Task("Walk", 30, frequency="daily", due_date=today)
    pet.add_task(walk)
    scheduler = Scheduler(make_owner(pet), day=today)
    scheduler.mark_task_complete(pet.id, walk.id)

    pending_today = scheduler.filter_tasks(completed=False, due_by=today)
    pending_any_day = scheduler.filter_tasks(completed=False)

    assert pending_today == []
    assert len(pending_any_day) == 1


# --- Recurring tasks ---------------------------------------------------------

def test_completing_daily_task_creates_one_due_tomorrow():
    today = date(2026, 10, 19)
    pet = Pet("Biscuit", "dog")
    walk = Task("Walk", 30, time="07:30", frequency="daily", due_date=today)
    pet.add_task(walk)
    scheduler = Scheduler(make_owner(pet), day=today)

    next_walk = scheduler.mark_task_complete(pet.id, walk.id)

    assert walk.completed is True
    assert next_walk is not None
    assert next_walk.due_date == today + timedelta(days=1)
    assert next_walk.completed is False
    assert next_walk.id != walk.id
    assert next_walk in pet.tasks


def test_late_completion_rolls_next_due_date_forward():
    pet = Pet("Biscuit", "dog")
    walk = Task("Walk", 30, frequency="daily", due_date=date(2026, 10, 16))
    pet.add_task(walk)
    scheduler = Scheduler(make_owner(pet), day=date(2026, 10, 19))  # 3 days late

    next_walk = scheduler.mark_task_complete(pet.id, walk.id)

    assert next_walk.due_date == date(2026, 10, 20)


def test_mark_task_complete_unknown_pet_returns_none():
    pet = Pet("Biscuit", "dog")
    task = Task("Walk", 30, frequency="daily")
    pet.add_task(task)
    scheduler = Scheduler(make_owner(pet))

    assert scheduler.mark_task_complete("no-such-pet", task.id) is None
    assert task.completed is False


# --- Conflict detection ------------------------------------------------------

def test_task_overlaps():
    walk = Task("Walk", 30, time="07:30")             # 07:30-08:00
    inside = Task("Ear drops", 5, time="07:45")
    back_to_back = Task("Breakfast", 10, time="08:00")
    untimed = Task("Play", 20)

    assert walk.overlaps(inside) and inside.overlaps(walk)  # symmetric
    assert not walk.overlaps(back_to_back)                  # touching ends are fine
    assert not walk.overlaps(untimed) and not untimed.overlaps(walk)


def test_detect_conflicts_flags_overlapping_durations():
    biscuit = Pet("Biscuit", "dog")
    luna = Pet("Luna", "cat")
    biscuit.add_task(Task("Walk", 30, time="07:30"))   # 07:30-08:00
    luna.add_task(Task("Ear drops", 5, time="07:45"))  # starts inside the walk
    scheduler = Scheduler(make_owner(biscuit, luna))

    warnings = scheduler.detect_conflicts(scheduler.owner.get_all_tasks())

    assert len(warnings) == 1
    assert "Walk" in warnings[0] and "Ear drops" in warnings[0]


def test_detect_conflicts_ignores_back_to_back_and_untimed_tasks():
    pet = Pet("Biscuit", "dog")
    pet.add_task(Task("Walk", 30, time="07:30"))       # ends 08:00
    pet.add_task(Task("Breakfast", 10, time="08:00"))  # starts exactly at 08:00
    pet.add_task(Task("Play", 20))                     # untimed
    scheduler = Scheduler(make_owner(pet))

    assert scheduler.detect_conflicts(scheduler.owner.get_all_tasks()) == []


def test_detect_conflicts_catches_task_nested_inside_a_long_one():
    pet = Pet("Biscuit", "dog")
    pet.add_task(Task("Grooming", 120, time="10:00"))  # 10:00-12:00
    pet.add_task(Task("Snack", 5, time="10:30"))
    pet.add_task(Task("Meds", 5, time="11:00"))
    scheduler = Scheduler(make_owner(pet))

    warnings = scheduler.detect_conflicts(scheduler.owner.get_all_tasks())

    assert len(warnings) == 2  # both overlap Grooming, not each other
