import pytest

from scheduler import Lesson, Slot, schedule


def test_separates_conflicting_teacher_and_group():
    lessons = [Lesson("A", "Иванов", "Математика"), Lesson("A", "Иванов", "Физика")]
    slots = [Slot("Пн", 1, "101"), Slot("Пн", 2, "101")]
    result = schedule(lessons, slots)
    assert result[lessons[0]].period != result[lessons[1]].period


def test_allows_parallel_lessons_in_different_rooms():
    lessons = [Lesson("A", "Иванов", "Математика"), Lesson("B", "Петров", "Физика")]
    slots = [Slot("Пн", 1, "101"), Slot("Пн", 1, "102")]
    result = schedule(lessons, slots)
    assert {slot.period for slot in result.values()} == {1}


def test_rejects_unschedulable_input():
    with pytest.raises(ValueError, match="Нет свободного"):
        schedule([Lesson("A", "Иванов", "Математика")], [])


def test_rejects_duplicate_lessons():
    lesson = Lesson("A", "Иванов", "Математика")
    with pytest.raises(ValueError, match="уникальными"):
        schedule([lesson, lesson], [Slot("Пн", 1, "101")])
