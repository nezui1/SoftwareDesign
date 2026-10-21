"""Простой детерминированный планировщик без внешних зависимостей."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Lesson:
    group: str
    teacher: str
    subject: str


@dataclass(frozen=True)
class Slot:
    day: str
    period: int
    room: str


def schedule(lessons: list[Lesson], slots: list[Slot]) -> dict[Lesson, Slot]:
    """Назначить первый допустимый слот каждому занятию.

    Возбуждает ValueError, если данных недостаточно для полного расписания.
    Одинаковые Lesson считаются одним занятием; для повторов нужен уникальный ID.
    """
    if len(set(lessons)) != len(lessons):
        raise ValueError("Занятия должны быть уникальными")
    result: dict[Lesson, Slot] = {}
    for lesson in lessons:
        for slot in slots:
            occupied = [
                (other, assigned)
                for other, assigned in result.items()
                if (assigned.day, assigned.period) == (slot.day, slot.period)
            ]
            if any(
                other.group == lesson.group
                or other.teacher == lesson.teacher
                or assigned.room == slot.room
                for other, assigned in occupied
            ):
                continue
            result[lesson] = slot
            break
        else:
            raise ValueError(f"Нет свободного слота для {lesson.subject}")
    return result
