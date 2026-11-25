#!/usr/bin/env python3
"""Find and classify design/implementation PRs linked to a GitHub Issue via gh CLI."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

DESIGN_DOC_NAMES = {"requirements.md", "specification.md", "architecture.md"}
DESIGN_SUBDIRS = {"requirements", "specification", "architecture"}


def run_gh(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(["gh", *args], text=True, capture_output=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def is_design_doc_path(file_path: str, design_paths: set[str]) -> bool:
    norm = Path(file_path).as_posix().lstrip("./")
    if design_paths:
        for dp in design_paths:
            dp_norm = Path(dp).as_posix().lstrip("./").rstrip("/")
            if norm == dp_norm or norm.startswith(dp_norm + "/"):
                return True
        return False
    p = Path(norm)
    if p.name in DESIGN_DOC_NAMES:
        return True
    if p.parent.name in DESIGN_SUBDIRS and p.suffix == ".md":
        return True
    return False


def get_diff_files(pr_number: int) -> list[str]:
    code, out, _ = run_gh(["pr", "diff", str(pr_number), "--name-only"])
    if code != 0:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Find PRs linked to an Issue by standalone Refs/Closes lines.")
    parser.add_argument("issue", type=int, help="GitHub Issue number")
    parser.add_argument("--state", choices=("open", "merged"), default="open", help="PR state to search")
    parser.add_argument(
        "--design-doc",
        action="append",
        default=[],
        help="Known design document file or split directory path (repeatable)",
    )
    args = parser.parse_args()

    code, out, err = run_gh(
        [
            "pr",
            "list",
            "--state",
            args.state,
            "--search",
            f"#{args.issue} in:body",
            "--limit",
            "100",
            "--json",
            "number,title,body,isDraft,headRefName",
        ]
    )
    if code != 0:
        sys.stderr.write(f"error: gh pr list failed: {err.strip()}\n")
        return 1

    try:
        candidates = json.loads(out) if out.strip() else []
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"error: invalid JSON from gh pr list: {exc}\n")
        return 1

    marker_re = re.compile(rf"(?m)^(Refs|Closes) #{args.issue}\s*$")
    design_paths = set(args.design_doc)
    design_prs: list[dict[str, Any]] = []
    impl_prs: list[dict[str, Any]] = []
    matched_numbers: set[int] = set()

    for pr in candidates:
        body = pr.get("body") or ""
        if not marker_re.search(body):
            continue
        num = pr.get("number")
        matched_numbers.add(num)
        diff_files = get_diff_files(num)
        entry = {
            "number": num,
            "title": pr.get("title", ""),
            "isDraft": bool(pr.get("isDraft", False)),
            "headRefName": pr.get("headRefName", ""),
            "diffFiles": diff_files,
        }
        if diff_files and all(is_design_doc_path(f, design_paths) for f in diff_files):
            design_prs.append(entry)
        else:
            impl_prs.append(entry)

    fallback = []
    if not matched_numbers:
        for pr in candidates:
            fallback.append(
                {
                    "number": pr.get("number"),
                    "title": pr.get("title", ""),
                    "isDraft": bool(pr.get("isDraft", False)),
                    "headRefName": pr.get("headRefName", ""),
                }
            )

    result = {
        "issue": args.issue,
        "state": args.state,
        "design_prs": design_prs,
        "impl_prs": impl_prs,
        "fallback_candidates": fallback,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
