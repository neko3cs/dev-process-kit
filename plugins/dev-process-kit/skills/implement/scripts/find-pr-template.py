#!/usr/bin/env python3
"""Locate Pull Request templates in the local repository or owner's .github repository."""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SINGLE_CANDIDATES = (
    ".github/pull_request_template.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "pull_request_template.md",
    "PULL_REQUEST_TEMPLATE.md",
    "docs/pull_request_template.md",
    "docs/PULL_REQUEST_TEMPLATE.md",
)


def run_gh(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(["gh", *args], text=True, capture_output=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def find_local_templates(root: Path) -> list[dict[str, str]]:
    for rel in SINGLE_CANDIDATES:
        p = root / rel
        if p.is_file():
            return [{"path": rel, "content": p.read_text(encoding="utf-8", errors="replace")}]

    tmpl_dir = root / ".github" / "PULL_REQUEST_TEMPLATE"
    if tmpl_dir.is_dir():
        found: list[dict[str, str]] = []
        for p in sorted(tmpl_dir.glob("*.md")):
            if p.is_file():
                found.append(
                    {
                        "path": p.relative_to(root).as_posix(),
                        "content": p.read_text(encoding="utf-8", errors="replace"),
                    }
                )
        if found:
            return found
    return []


def resolve_owner(repo_arg: str | None) -> str | None:
    if repo_arg and "/" in repo_arg:
        return repo_arg.split("/", 1)[0]
    code, out, _ = run_gh(["repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"])
    if code == 0 and "/" in out.strip():
        return out.strip().split("/", 1)[0]
    return None


def fetch_remote_template(owner: str) -> list[dict[str, str]]:
    for rel in (".github/pull_request_template.md", ".github/PULL_REQUEST_TEMPLATE.md"):
        code, out, _ = run_gh(["api", f"repos/{owner}/.github/contents/{rel}"])
        if code != 0:
            continue
        try:
            payload = json.loads(out)
            content = base64.b64decode(payload.get("content", "")).decode("utf-8", errors="replace")
            return [{"path": f"{owner}/.github:{rel}", "content": content}]
        except (json.JSONDecodeError, ValueError):
            continue
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Find PR templates locally or in owner/.github.")
    parser.add_argument("-R", "--repo", help="Target repository in owner/repo format")
    parser.add_argument("--root", default=".", help="Repository root directory")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    local = find_local_templates(root)
    if local:
        result: dict[str, Any] = {"found": True, "source": "local", "templates": local}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    owner = resolve_owner(args.repo)
    remote = fetch_remote_template(owner) if owner else []
    result = {
        "found": bool(remote),
        "source": f"{owner}/.github" if remote and owner else None,
        "templates": remote,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
