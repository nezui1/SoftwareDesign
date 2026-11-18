"""Собрать проверяемые показатели репозитория для отчета о прототипе."""

import json
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> None:
    activity: dict[str, dict[str, int]] = defaultdict(
        lambda: {"commits": 0, "added_lines": 0, "deleted_lines": 0}
    )
    for commit, date in (
        line.split(" ", 1)
        for line in git("log", "--format=%H %cs", "--no-merges").splitlines()
    ):
        week = datetime.fromisoformat(date).strftime("%G-W%V")
        activity[week]["commits"] += 1
        for line in git("show", "--format=", "--numstat", commit).splitlines():
            parts = line.split("\t")
            if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
                activity[week]["added_lines"] += int(parts[0])
                activity[week]["deleted_lines"] += int(parts[1])

    source = list((ROOT / "scheduler_lab" / "scheduler").rglob("*.py"))
    source += list((ROOT / "scheduler_lab" / "scheduler" / "prototype").glob("*.html"))
    tests = list((ROOT / "scheduler_lab" / "tests").glob("test_*.py"))
    data = {
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "branch": git("branch", "--show-current"),
        "commit": git("rev-parse", "HEAD"),
        "scope": "Только подтверждаемые показатели Git и файлов рабочей ветки",
        "weekly_git_activity": dict(sorted(activity.items())),
        "project_size": {
            "source_files": len(source),
            "source_lines": sum(len(p.read_text(encoding="utf-8").splitlines()) for p in source),
            "test_files": len(tests),
            "test_lines": sum(len(p.read_text(encoding="utf-8").splitlines()) for p in tests),
        },
        "tracker_task_counts": None,
        "tracker_burndown": None,
        "actual_hours": None,
        "unavailable_reason": "Экспорт задач и трудозатрат YouGile не предоставлен",
    }
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
