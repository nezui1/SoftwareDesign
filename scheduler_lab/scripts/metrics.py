"""Снимок простых метрик кода и Git в JSON."""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def main() -> None:
    code_lines = sum(
        len(path.read_text(encoding="utf-8").splitlines())
        for path in (ROOT / "scheduler").rglob("*.py")
    )
    commits = git("log", "--since=7 days ago", "--format=%H").splitlines()
    sizes = []
    for commit in commits:
        stat = git("show", "--format=", "--numstat", commit)
        size = sum(
            int(parts[0]) + int(parts[1])
            for line in stat.splitlines()
            if len(parts := line.split("\t")) >= 2
            and parts[0].isdigit()
            and parts[1].isdigit()
        )
        sizes.append(size)
    metrics = {
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_lines": code_lines,
        "commits_last_7_days": len(commits),
        "mean_commit_changed_lines": round(sum(sizes) / len(sizes), 1)
        if sizes
        else 0,
    }
    lint_file = ROOT / "lint.txt"
    if lint_file.exists():
        lint = lint_file.read_text(encoding="utf-8")
        metrics["lint_findings"] = 0 if "All checks passed!" in lint else None
    coverage_file = ROOT / "coverage.xml"
    if coverage_file.exists():
        coverage = ElementTree.parse(coverage_file).getroot()
        metrics["line_coverage_percent"] = round(
            float(coverage.attrib["line-rate"]) * 100, 1
        )
        metrics["branch_coverage_percent"] = round(
            float(coverage.attrib["branch-rate"]) * 100, 1
        )
    junit_file = ROOT / "junit.xml"
    if junit_file.exists():
        junit = ElementTree.parse(junit_file).getroot()
        suite = junit if junit.tag == "testsuite" else junit.find("testsuite")
        if suite is not None:
            total = int(suite.attrib.get("tests", 0))
            failed = int(suite.attrib.get("failures", 0)) + int(
                suite.attrib.get("errors", 0)
            )
            metrics["tests_passed"] = total - failed - int(
                suite.attrib.get("skipped", 0)
            )
            metrics["tests_failed"] = failed
            metrics["test_duration_seconds"] = round(
                float(suite.attrib.get("time", 0)), 3
            )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
