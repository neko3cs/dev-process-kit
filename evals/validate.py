#!/usr/bin/env python3
"""Validate evaluation scenario files under evals/scenarios/."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

VALID_SKILLS = {"issue", "design", "implement"}
REQUIRED_SCENARIO_KEYS = {"id", "title", "branch", "prompt_args", "setup", "expected"}


def load_all_scenarios(scenarios_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    all_scenarios: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    files = sorted(scenarios_dir.glob("*.json"))
    if not files:
        return [], [f"No scenario files found in {scenarios_dir}"]

    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}: invalid JSON: {exc}")
            continue

        skill = data.get("skill")
        if skill not in VALID_SKILLS:
            errors.append(f"{path.name}: 'skill' must be one of {sorted(VALID_SKILLS)}, got {skill!r}")
            continue

        scenarios = data.get("scenarios")
        if not isinstance(scenarios, list) or not scenarios:
            errors.append(f"{path.name}: 'scenarios' must be a non-empty list")
            continue

        for idx, sc in enumerate(scenarios):
            prefix = f"{path.name}[{idx}]"
            if not isinstance(sc, dict):
                errors.append(f"{prefix}: scenario must be an object")
                continue

            missing = REQUIRED_SCENARIO_KEYS - set(sc.keys())
            if missing:
                errors.append(f"{prefix}: missing required keys: {sorted(missing)}")
                continue

            sid = sc["id"]
            if not isinstance(sid, str) or not re.match(r"^[a-z0-9][a-z0-9-]*$", sid):
                errors.append(f"{prefix}: invalid id {sid!r}")
            elif sid in seen_ids:
                errors.append(f"{prefix}: duplicate scenario id {sid!r}")
            else:
                seen_ids.add(sid)

            expected = sc["expected"]
            if not isinstance(expected, dict):
                errors.append(f"{prefix} ({sid}): 'expected' must be an object")
            else:
                for k in ("summary",):
                    if not isinstance(expected.get(k), str) or not expected[k].strip():
                        errors.append(f"{prefix} ({sid}): expected.{k} must be a non-empty string")
                for k in ("must", "must_not"):
                    val = expected.get(k)
                    if not isinstance(val, list) or not val or not all(isinstance(x, str) and x.strip() for x in val):
                        errors.append(f"{prefix} ({sid}): expected.{k} must be a non-empty list of strings")

                checks = expected.get("checks", {})
                if not isinstance(checks, dict):
                    errors.append(f"{prefix} ({sid}): expected.checks must be an object")
                else:
                    for key in ("gh_must_call", "gh_must_not_call"):
                        patterns = checks.get(key, [])
                        if not isinstance(patterns, list):
                            errors.append(f"{prefix} ({sid}): checks.{key} must be a list")
                            continue
                        for pat in patterns:
                            try:
                                re.compile(pat)
                            except re.error as exc:
                                errors.append(f"{prefix} ({sid}): invalid regex in checks.{key}: {pat!r} ({exc})")

            sc_copy = dict(sc)
            sc_copy["skill"] = skill
            all_scenarios.append(sc_copy)

    return all_scenarios, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate dev-process-kit evaluation scenarios.")
    parser.add_argument("--list", action="store_true", help="Print a table of all scenarios")
    parser.add_argument("--skill", choices=sorted(VALID_SKILLS), help="Filter by skill when listing")
    args = parser.parse_args()

    scenarios_dir = Path(__file__).resolve().parent / "scenarios"
    scenarios, errors = load_all_scenarios(scenarios_dir)

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    if args.list:
        filtered = [s for s in scenarios if not args.skill or s["skill"] == args.skill]
        print(f"{'SKILL':<10} {'ID':<42} {'TITLE'}")
        print("-" * 96)
        for s in filtered:
            print(f"{s['skill']:<10} {s['id']:<42} {s['title']}")
        print(f"\nTotal: {len(filtered)} scenario(s)")
        return 0

    counts: dict[str, int] = {}
    for s in scenarios:
        counts[s["skill"]] = counts.get(s["skill"], 0) + 1
    summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    print(f"All {len(scenarios)} evaluation scenarios are valid ({summary}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
