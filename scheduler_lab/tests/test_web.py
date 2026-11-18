"""Проверки HTTP-прототипа через реальные запросы к локальному серверу."""

import json
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from threading import Thread

import pytest

from scheduler.web import Handler


@pytest.fixture
def server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield httpd.server_address[1]
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)


def request(port, method, path, payload=None):
    connection = HTTPConnection("127.0.0.1", port, timeout=3)
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if body else {}
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    content = response.read()
    connection.close()
    return response.status, content


def test_page_contains_form_and_action(server):
    status, content = request(server, "GET", "/")
    page = content.decode("utf-8")
    assert status == 200
    assert "Генератор учебного расписания" in page
    assert 'id="lessons"' in page
    assert 'id="generate"' in page


def test_api_generates_schedule_without_group_conflict(server):
    payload = {
        "lessons": [
            {"group": "A", "teacher": "Иванов", "subject": "Математика"},
            {"group": "A", "teacher": "Петров", "subject": "Физика"},
        ],
        "slots": [
            {"day": "Пн", "period": 1, "room": "101"},
            {"day": "Пн", "period": 2, "room": "101"},
        ],
    }
    status, content = request(server, "POST", "/api/schedule", payload)
    result = json.loads(content)
    assert status == 200
    assert len(result["schedule"]) == 2
    assert {item["period"] for item in result["schedule"]} == {1, 2}


def test_api_reports_unschedulable_input(server):
    payload = {
        "lessons": [{"group": "A", "teacher": "Иванов", "subject": "Математика"}],
        "slots": [],
    }
    status, content = request(server, "POST", "/api/schedule", payload)
    assert status == 400
    assert "Нет свободного" in json.loads(content)["error"]


def test_api_rejects_incomplete_payload(server):
    status, content = request(server, "POST", "/api/schedule", {"lessons": []})
    assert status == 400
    assert "error" in json.loads(content)


def test_unknown_page_returns_404(server):
    status, _ = request(server, "GET", "/missing")
    assert status == 404


def test_unknown_api_returns_404(server):
    status, _ = request(server, "POST", "/missing", {"lessons": [], "slots": []})
    assert status == 404


def test_invalid_json_returns_400(server):
    connection = HTTPConnection("127.0.0.1", server, timeout=3)
    connection.request("POST", "/api/schedule", body="{broken", headers={
        "Content-Type": "application/json"
    })
    response = connection.getresponse()
    content = response.read()
    connection.close()
    assert response.status == 400
    assert "error" in json.loads(content)
