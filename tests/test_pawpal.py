from pawpal_system import Pet, Task


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
