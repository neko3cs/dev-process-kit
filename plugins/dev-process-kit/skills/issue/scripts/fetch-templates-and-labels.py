#!/usr/bin/env python3
"""Fetch GitHub Issue templates (excluding config.yml) and repository labels via gh CLI."""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

TEMPLATE_EXTS = {".md", ".yml", ".yaml"}
EXCLUDED_NAMES = {"config.yml", "config.yaml"}


def run_gh(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(["gh", *args], text=True, capture_output=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def resolve_repo(repo_arg: str | None) -> str:
    if repo_arg:
        return repo_arg
    code, out, err = run_gh(["repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"])
    if code != 0 or not out.strip():
        raise RuntimeError(f"failed to resolve repository: {err.strip()}")
    return out.strip()


def fetch_templates_from(repo: str) -> list[dict[str, str]] | None:
    code, out, _ = run_gh(["api", f"repos/{repo}/contents/.github/ISSUE_TEMPLATE"])
    if code != 0:
        return None
    try:
        entries = json.loads(out)
    except json.JSONDecodeError:
        return None
    if not isinstance(entries, list):
        return None

    templates: list[dict[str, str]] = []
    for entry in entries:
        name = entry.get("name", "") if isinstance(entry, dict) else str(entry)
        lower = name.lower()
        if lower in EXCLUDED_NAMES or Path(lower).suffix not in TEMPLATE_EXTS:
            continue
        f_code, f_out, _ = run_gh(["api", f"repos/{repo}/contents/.github/ISSUE_TEMPLATE/{name}"])
        if f_code != 0:
            continue
        try:
            payload = json.loads(f_out)
            raw_b64 = payload.get("content", "")
            content = base64.b64decode(raw_b64).decode("utf-8", errors="replace")
        except (json.JSONDecodeError, ValueError):
            continue
        templates.append({"name": name, "content": content})
    return templates


def fetch_labels(repo: str, explicit_repo: str | None) -> list[str]:
    args = ["label", "list", "--limit", "1000", "--json", "name"]
    if explicit_repo:
        args[2:2] = ["-R", explicit_repo]
    code, out, _ = run_gh(args)
    if code != 0:
        return []
    try:
        items = json.loads(out)
    except json.JSONDecodeError:
        return []
    return [it["name"] for it in items if isinstance(it, dict) and "name" in it]


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Issue templates and labels for a GitHub repository.")
    parser.add_argument("-R", "--repo", help="Target repository in owner/repo format")
    parser.add_argument("--check-labels", help="Comma-separated label names to verify case-insensitively")
    args = parser.parse_args()

    try:
        repo = resolve_repo(args.repo)
    except RuntimeError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1

    owner = repo.split("/", 1)[0]
    source: str | None = None
    templates = fetch_templates_from(repo)
    if templates:
        source = repo
    else:
        fallback_repo = f"{owner}/.github"
        fallback_templates = fetch_templates_from(fallback_repo)
        if fallback_templates:
            templates = fallback_templates
            source = fallback_repo
        else:
            templates = []

    labels = fetch_labels(repo, args.repo)
    result: dict[str, Any] = {
        "repo": repo,
        "template_source": source,
        "templates": templates,
        "labels": labels,
    }

    if args.check_labels is not None:
        canonical = {lbl.lower(): lbl for lbl in labels}
        valid: list[str] = []
        missing: list[str] = []
        for raw in args.check_labels.split(","):
            name = raw.strip()
            if not name:
                continue
            matched = canonical.get(name.lower())
            if matched is not None:
                valid.append(matched)
            else:
                missing.append(name)
        result["label_check"] = {"valid": valid, "missing": missing}

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
