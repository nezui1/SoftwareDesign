"""Минимальный HTTP-прототип для демонстрации генерации расписания."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from scheduler.core import Lesson, Slot, schedule

PAGE = Path(__file__).resolve().parent / "prototype" / "index.html"


def generate(payload: dict) -> list[dict]:
    """Преобразовать JSON-запрос в расписание для интерфейса."""
    lessons = [Lesson(**item) for item in payload["lessons"]]
    slots = [Slot(**item) for item in payload["slots"]]
    result = schedule(lessons, slots)
    return [
        {
            "group": lesson.group,
            "teacher": lesson.teacher,
            "subject": lesson.subject,
            "day": slot.day,
            "period": slot.period,
            "room": slot.room,
        }
        for lesson, slot in result.items()
    ]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/":
            self.send_error(404)
            return
        content = PAGE.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        if self.path != "/api/schedule":
            self.send_error(404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > 100_000:
                raise ValueError("Некорректный размер запроса")
            payload = json.loads(self.rfile.read(size))
            result = {"schedule": generate(payload)}
            status = 200
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            result = {"error": str(exc)}
            status = 400
        content = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("Прототип: http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
