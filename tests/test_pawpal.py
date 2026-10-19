from datetime import date, timedelta

import pytest

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


def test_detect_conflicts_ignores_other_days_and_completed_tasks():
    today = date(2026, 10, 19)
    pet = Pet("Biscuit", "dog")
    walk = Task("Walk", 30, time="07:30", frequency="daily", due_date=today)
    pet.add_task(walk)
    pet.add_task(Task("Vet", 60, time="07:00", due_date=today + timedelta(days=2)))
    scheduler = Scheduler(make_owner(pet), day=today)
    scheduler.mark_task_complete(pet.id, walk.id)  # adds tomorrow's 07:30 walk

    # Done walk (today) and new walk (tomorrow) share a time slot; vet is another day.
    assert scheduler.detect_conflicts(scheduler.owner.get_all_tasks()) == []


def test_detect_conflicts_flags_same_start_time():
    today = date(2026, 10, 19)
    pet = Pet("Biscuit", "dog")
    pet.add_task(Task("Breakfast", 10, time="08:00", due_date=today))
    pet.add_task(Task("Meds", 5, time="08:00", due_date=today))
    scheduler = Scheduler(make_owner(pet), day=today)

    assert len(scheduler.detect_conflicts(scheduler.owner.get_all_tasks())) == 1


def test_detect_conflicts_three_way_overlap_reports_every_pair():
    today = date(2026, 10, 19)
    pet = Pet("Biscuit", "dog")
    pet.add_task(Task("A", 60, time="09:00", due_date=today))  # 09:00-10:00
    pet.add_task(Task("B", 60, time="09:15", due_date=today))  # 09:15-10:15
    pet.add_task(Task("C", 60, time="09:30", due_date=today))  # 09:30-10:30
    scheduler = Scheduler(make_owner(pet), day=today)

    assert len(scheduler.detect_conflicts(scheduler.owner.get_all_tasks())) == 3


def test_conflicting_pairs_returns_overlapping_pairs_earlier_task_first():
    today = date(2026, 10, 19)
    biscuit = Pet("Biscuit", "dog")
    luna = Pet("Luna", "cat")
    drops = Task("Ear drops", 5, time="07:45", due_date=today)
    walk = Task("Walk", 30, time="07:30", due_date=today)                  # 07:30-08:00
    overdue = Task("Brush", 10, time="07:50", due_date=today - timedelta(days=1))
    done = Task("Breakfast", 10, time="07:40", due_date=today)
    done.mark_complete()
    luna.add_task(drops)  # added first, but starts later
    biscuit.add_task(walk)
    biscuit.add_task(overdue)
    biscuit.add_task(done)
    scheduler = Scheduler(make_owner(biscuit, luna), day=today)
    tasks = scheduler.owner.get_all_tasks()

    # Overdue Brush has a different due date; completed Breakfast is ignored.
    assert scheduler.conflicting_pairs(tasks) == [((biscuit, walk), (luna, drops))]
    # same_day treats every task as today, so Brush now clashes with Walk.
    assert scheduler.conflicting_pairs(tasks, same_day=True) == [
        ((biscuit, walk), (luna, drops)),
        ((biscuit, walk), (biscuit, overdue)),
    ]
    assert scheduler.conflicting_pairs([]) == []


def test_tasks_crossing_midnight_are_not_detected():
    # Known limitation: times are minutes since midnight with no wraparound, so a
    # task running past midnight never conflicts with an early-morning task, and
    # its end time is shown as "24:30".
    today = date(2026, 10, 19)
    pet = Pet("Biscuit", "dog")
    pet.add_task(Task("Late walk", 60, time="23:30", due_date=today))  # "ends" 24:30
    pet.add_task(Task("Night meds", 5, time="00:15", due_date=today))
    scheduler = Scheduler(make_owner(pet), day=today)

    assert pet.tasks[0].end_minutes == 24 * 60 + 30
    assert scheduler.detect_conflicts(scheduler.owner.get_all_tasks()) == []


# --- Plan generation ---------------------------------------------------------

DAY = date(2026, 10, 19)


def plan_for(tasks, available_minutes=120, day=DAY):
    pet = Pet("Biscuit", "dog")
    for task in tasks:
        pet.add_task(task)
    owner = make_owner(pet)
    owner.available_minutes = available_minutes
    return Scheduler(owner, day=day).generate_plan()


def test_plan_schedules_tasks_that_exactly_fill_the_budget():
    plan = plan_for(
        [Task("Walk", 30, due_date=DAY), Task("Play", 30, due_date=DAY)],
        available_minutes=60,
    )

    assert sorted(titles(plan.scheduled)) == ["Play", "Walk"]
    assert plan.skipped == []
    assert plan.minutes_used == 60


def test_plan_skips_task_that_does_not_fit_and_keeps_going():
    plan = plan_for(
        [
            Task("Walk", 20, "high", due_date=DAY),
            Task("Groom", 20, "medium", due_date=DAY),
            Task("Brush", 10, "low", due_date=DAY),
        ],
        available_minutes=30,
    )

    assert sorted(titles(plan.scheduled)) == ["Brush", "Walk"]
    assert [task.title for _, task, _ in plan.skipped] == ["Groom"]
    assert plan.skipped[0][2] == "not enough time (needs 20 min, 10 min left)"
    assert plan.minutes_used == 30


def test_plan_includes_overdue_and_excludes_future_and_completed_tasks():
    done = Task("Done", 10, due_date=DAY)
    done.mark_complete()
    plan = plan_for([
        Task("Overdue", 10, due_date=DAY - timedelta(days=2)),
        Task("Today", 10, due_date=DAY),
        Task("Tomorrow", 10, due_date=DAY + timedelta(days=1)),
        done,
    ])

    assert sorted(titles(plan.scheduled)) == ["Overdue", "Today"]
    assert plan.skipped == []
    assert plan.minutes_used == 20


def test_plan_output_is_in_time_order_not_priority_order():
    plan = plan_for([
        Task("High late", 10, "high", time="09:00", due_date=DAY),
        Task("Untimed", 10, "high", due_date=DAY),
        Task("Low early", 10, "low", time="07:00", due_date=DAY),
    ])

    assert titles(plan.scheduled) == ["Low early", "High late", "Untimed"]


def test_plan_flags_overdue_task_clashing_with_todays_task():
    pet = Pet("Biscuit", "dog")
    pet.add_task(Task("Overdue meds", 10, "high", time="08:00", due_date=DAY - timedelta(days=1)))
    pet.add_task(Task("Breakfast", 10, "high", time="08:00", due_date=DAY))
    scheduler = Scheduler(make_owner(pet), day=DAY)

    plan = scheduler.generate_plan()
    warnings = scheduler.detect_conflicts(plan.scheduled, same_day=True)

    assert sorted(titles(plan.scheduled)) == ["Breakfast", "Overdue meds"]
    assert len(warnings) == 1
    assert "Overdue meds" in warnings[0] and "Breakfast" in warnings[0]
    assert "Warnings:" in scheduler.explain_plan(plan)
    # Without same_day, different due dates mean no conflict.
    assert scheduler.detect_conflicts(plan.scheduled) == []


def test_plan_with_no_pets_is_empty():
    plan = Scheduler(Owner("Jordan"), day=DAY).generate_plan()

    assert plan.scheduled == [] and plan.skipped == [] and plan.minutes_used == 0


def test_plan_with_no_tasks_is_empty():
    plan = plan_for([])

    assert plan.scheduled == [] and plan.skipped == [] and plan.minutes_used == 0


def test_plan_with_zero_minutes_skips_everything():
    plan = plan_for([Task("Walk", 30, due_date=DAY)], available_minutes=0)

    assert plan.scheduled == []
    assert titles((p, t) for p, t, _ in plan.skipped) == ["Walk"]
    assert plan.minutes_used == 0


# --- More recurrence ---------------------------------------------------------

def complete_once(task, day=DAY):
    pet = Pet("Biscuit", "dog")
    pet.add_task(task)
    scheduler = Scheduler(make_owner(pet), day=day)
    return pet, scheduler, scheduler.mark_task_complete(pet.id, task.id)


def test_completing_weekly_task_creates_one_due_next_week():
    _, _, next_task = complete_once(Task("Bath", 30, frequency="weekly", due_date=DAY))

    assert next_task.due_date == DAY + timedelta(days=7)


def test_completing_one_off_task_creates_nothing():
    task = Task("Vet", 60, due_date=DAY)
    pet, _, next_task = complete_once(task)

    assert next_task is None
    assert task.completed is True
    assert pet.tasks == [task]


def test_completing_same_task_twice_creates_only_one_occurrence():
    task = Task("Walk", 30, frequency="daily", due_date=DAY)
    pet, scheduler, _ = complete_once(task)

    assert scheduler.mark_task_complete(pet.id, task.id) is None
    assert len(pet.tasks) == 2


def test_mark_task_complete_unknown_task_returns_none():
    task = Task("Walk", 30, frequency="daily", due_date=DAY)
    pet = Pet("Biscuit", "dog")
    pet.add_task(task)
    scheduler = Scheduler(make_owner(pet), day=DAY)

    assert scheduler.mark_task_complete(pet.id, "no-such-task") is None
    assert len(pet.tasks) == 1


def test_early_completion_counts_from_due_date():
    task = Task("Walk", 30, frequency="daily", due_date=DAY + timedelta(days=2))

    _, _, next_task = complete_once(task, day=DAY)  # done 2 days early

    assert next_task.due_date == DAY + timedelta(days=3)


def test_next_occurrence_copies_task_details():
    task = Task("Walk", 30, "high", "walk", time="07:30", frequency="daily", due_date=DAY)

    _, _, next_task = complete_once(task)

    assert (next_task.title, next_task.duration_minutes, next_task.priority,
            next_task.category, next_task.time, next_task.frequency) == (
        "Walk", 30, "high", "walk", "07:30", "daily")


def test_recurrence_rolls_over_month_and_year():
    new_years_eve = date(2026, 12, 31)
    _, _, next_task = complete_once(
        Task("Walk", 30, frequency="daily", due_date=new_years_eve), day=new_years_eve
    )

    assert next_task.due_date == date(2027, 1, 1)


# --- Validation --------------------------------------------------------------

@pytest.mark.parametrize("duration", [0, -30])
def test_task_rejects_non_positive_duration(duration):
    with pytest.raises(ValueError):
        Task("Walk", duration)


@pytest.mark.parametrize("bad_time", ["9:05", "7:5", "24:00", "12:60", "noon", ""])
def test_task_rejects_malformed_time(bad_time):
    with pytest.raises(ValueError):
        Task("Walk", 30, time=bad_time)


@pytest.mark.parametrize("good_time", ["00:00", "09:05", "23:59"])
def test_task_accepts_valid_time(good_time):
    assert Task("Walk", 30, time=good_time).time == good_time


def test_task_rejects_unknown_priority():
    with pytest.raises(ValueError):
        Task("Walk", 30, priority="High")  # case matters


def test_task_rejects_unknown_frequency():
    with pytest.raises(ValueError):
        Task("Walk", 30, frequency="monthly")


# --- Next available slot -----------------------------------------------------

def slot_scheduler(*times_and_durations):
    """Scheduler whose plan holds one timed task per (time, minutes) pair."""
    pet = Pet("Biscuit", "dog")
    for hhmm, minutes in times_and_durations:
        pet.add_task(Task(f"Task {hhmm}", minutes, time=hhmm, due_date=DAY))
    owner = make_owner(pet)
    owner.available_minutes = 1440
    return Scheduler(owner, day=DAY)


def test_next_slot_on_empty_day_is_day_start():
    scheduler = slot_scheduler()

    assert scheduler.find_next_available_slot(30) == "07:00"
    assert scheduler.find_next_available_slot(30, day_start="09:15") == "09:15"


def test_next_slot_finds_first_gap_big_enough():
    scheduler = slot_scheduler(("07:00", 60), ("08:30", 30), ("10:00", 15))  # gaps: 08:00-08:30, 09:00-10:00

    assert scheduler.find_next_available_slot(30) == "08:00"  # exactly fills the first gap
    assert scheduler.find_next_available_slot(45) == "09:00"  # first gap too small
    assert scheduler.find_next_available_slot(90) == "10:15"  # only room after the last task


def test_next_slot_ignores_untimed_completed_and_unscheduled_tasks():
    pet = Pet("Biscuit", "dog")
    done = Task("Done", 60, time="07:00", due_date=DAY)
    done.mark_complete()
    pet.add_task(done)
    pet.add_task(Task("Untimed", 60, due_date=DAY))
    pet.add_task(Task("Tomorrow", 60, time="07:00", due_date=DAY + timedelta(days=1)))
    scheduler = Scheduler(make_owner(pet), day=DAY)

    assert scheduler.find_next_available_slot(30) == "07:00"


def test_next_slot_returns_none_when_no_room_left():
    scheduler = slot_scheduler(("07:00", 600), ("17:00", 210))  # back to back; only 20:30-21:00 free

    assert scheduler.find_next_available_slot(30) == "20:30"  # ends exactly at day_end
    assert scheduler.find_next_available_slot(31) is None
    assert slot_scheduler(("07:00", 840)).find_next_available_slot(5) is None  # fully booked


def test_next_slot_rejects_bad_input():
    scheduler = slot_scheduler()

    with pytest.raises(ValueError):
        scheduler.find_next_available_slot(0)
    with pytest.raises(ValueError):
        scheduler.find_next_available_slot(30, day_start="7:00")


def test_explain_plan_suggests_a_new_time_for_each_conflict():
    pet = Pet("Biscuit", "dog")
    pet.add_task(Task("Walk", 30, "high", time="07:30", due_date=DAY))      # 07:30-08:00
    pet.add_task(Task("Ear drops", 5, "high", time="07:45", due_date=DAY))
    pet.add_task(Task("Breakfast", 60, "high", time="07:00", due_date=DAY))  # 07:00-08:00, clashes too
    scheduler = Scheduler(make_owner(pet), day=DAY)

    text = scheduler.explain_plan(scheduler.generate_plan())

    # Walk and Ear drops both start inside Breakfast; Ear drops also inside Walk.
    assert "Try moving Walk to 08:00." in text
    assert text.count("Try moving Ear drops to 08:00.") == 2
