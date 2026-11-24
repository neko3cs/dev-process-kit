#!/usr/bin/env python3
"""Fixture-driven mock for the GitHub CLI (`gh`) used by dev-process-kit evals.

Reads state from EVAL_GH_STATE (JSON) and appends every invocation to
EVAL_GH_LOG (JSONL). Supports `--jq` by delegating to the system `jq` binary.
"""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def append_log(log_path: Path, entry: dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def extract_flag_value(args: list[str], *names: str) -> str | None:
    for i, arg in enumerate(args):
        if arg in names and i + 1 < len(args):
            return args[i + 1]
        for name in names:
            prefix = f"{name}="
            if arg.startswith(prefix):
                return arg[len(prefix) :]
    return None


def extract_flag_values(args: list[str], *names: str) -> list[str]:
    values: list[str] = []
    for i, arg in enumerate(args):
        if arg in names and i + 1 < len(args):
            values.append(args[i + 1])
        else:
            for name in names:
                prefix = f"{name}="
                if arg.startswith(prefix):
                    values.append(arg[len(prefix) :])
    return values


def has_flag(args: list[str], *names: str) -> bool:
    return any(arg in names for arg in args)


def read_body_from_args(args: list[str]) -> str | None:
    body = extract_flag_value(args, "--body", "-b")
    if body is not None:
        return body
    body_file = extract_flag_value(args, "--body-file", "-F")
    if body_file:
        if body_file == "-":
            return sys.stdin.read()
        p = Path(body_file)
        if p.exists():
            return p.read_text(encoding="utf-8")
    # `gh api ... -f body=...`
    for val in extract_flag_values(args, "-f", "--raw-field", "-F", "--field"):
        if val.startswith("body="):
            return val[len("body=") :]
    return None


def apply_jq(data: Any, jq_expr: str | None) -> str:
    text = json.dumps(data, ensure_ascii=False)
    if not jq_expr:
        return text
    proc = subprocess.run(
        ["jq", "-r", jq_expr],
        input=text,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        sys.exit(proc.returncode)
    return proc.stdout.rstrip("\n")


def filter_json_fields(item: dict[str, Any], fields_csv: str | None) -> dict[str, Any]:
    if not fields_csv:
        return item
    fields = [f.strip() for f in fields_csv.split(",") if f.strip()]
    return {k: item.get(k) for k in fields}


def format_issue_view(issue: dict[str, Any], include_comments: bool) -> str:
    lines = [
        f"title:\t{issue.get('title', '')}",
        f"state:\t{issue.get('state', 'OPEN')}",
        f"author:\t{issue.get('author', {}).get('login', 'user')}",
        f"labels:\t{', '.join(l.get('name', l) if isinstance(l, dict) else str(l) for l in issue.get('labels', []))}",
        f"number:\t{issue.get('number', '')}",
        "--",
        issue.get("body", ""),
    ]
    if include_comments and issue.get("comments"):
        lines.append("")
        lines.append("-- comments --")
        for c in issue["comments"]:
            author = c.get("author", {}).get("login", "user")
            cid = c.get("id", "")
            lines.append(f"author: {author} (id: {cid})")
            lines.append(c.get("body", ""))
            lines.append("---")
    return "\n".join(lines)


def format_pr_view(pr: dict[str, Any], include_comments: bool) -> str:
    lines = [
        f"title:\t{pr.get('title', '')}",
        f"state:\t{pr.get('state', 'OPEN')}",
        f"draft:\t{str(pr.get('isDraft', False)).lower()}",
        f"head:\t{pr.get('headRefName', '')}",
        f"number:\t{pr.get('number', '')}",
        "--",
        pr.get("body", ""),
    ]
    if include_comments and pr.get("comments"):
        lines.append("")
        lines.append("-- comments --")
        for c in pr["comments"]:
            author = c.get("author", {}).get("login", "user")
            cid = c.get("id", "")
            lines.append(f"author: {author} (id: {cid})")
            lines.append(c.get("body", ""))
            lines.append("---")
    if pr.get("reviews"):
        lines.append("")
        lines.append("-- reviews --")
        for r in pr["reviews"]:
            author = r.get("author", {}).get("login", "reviewer")
            lines.append(f"author: {author} state: {r.get('state', 'COMMENTED')}")
            lines.append(r.get("body", ""))
            lines.append("---")
    return "\n".join(lines)


def handle_issue(args: list[str], state: dict[str, Any], state_path: Path) -> int:
    if not args:
        sys.stderr.write("mock-gh: missing issue subcommand\n")
        return 1
    sub, rest = args[0], args[1:]
    repo = extract_flag_value(rest, "-R", "--repo") or state.get("repo", "example/app")
    issues: dict[str, dict[str, Any]] = state.setdefault("issues", {})
    jq_expr = extract_flag_value(rest, "--jq", "-q")
    json_fields = extract_flag_value(rest, "--json")

    if sub == "view":
        num = next((a for a in rest if not a.startswith("-")), "")
        num = num.lstrip("#")
        issue = issues.get(num)
        if not issue:
            sys.stderr.write(f"GraphQL: Could not resolve to an Issue with the number of {num}.\n")
            return 1
        if json_fields is not None:
            data = filter_json_fields(issue, json_fields)
            print(apply_jq(data, jq_expr))
        else:
            print(format_issue_view(issue, has_flag(rest, "--comments", "-c")))
        return 0

    if sub == "list":
        items = list(issues.values())
        search = extract_flag_value(rest, "--search", "-S")
        if search:
            terms = [t.lower() for t in search.split() if not t.startswith(("is:", "in:"))]
            items = [
                it
                for it in items
                if all(
                    t in (it.get("title", "") + "\n" + it.get("body", "")).lower()
                    for t in terms
                )
            ]
        if json_fields is not None:
            data = [filter_json_fields(it, json_fields) for it in items]
            print(apply_jq(data, jq_expr))
        else:
            for it in items:
                print(f"#{it.get('number')}\t{it.get('state', 'OPEN')}\t{it.get('title', '')}")
        return 0

    if sub == "create":
        existing_labels = {l.lower() for l in state.get("labels", [])}
        req_labels = extract_flag_values(rest, "--label", "-l")
        for lbl in req_labels:
            for part in lbl.split(","):
                p = part.strip()
                if p and existing_labels and p.lower() not in existing_labels:
                    sys.stderr.write(f"could not add label: '{p}' not found\n")
                    return 1
        next_num = max((int(k) for k in issues.keys() if k.isdigit()), default=100) + 1
        title = extract_flag_value(rest, "--title", "-t") or ""
        body = read_body_from_args(rest) or ""
        issues[str(next_num)] = {
            "number": next_num,
            "title": title,
            "body": body,
            "state": "OPEN",
            "labels": [{"name": l} for l in req_labels],
            "author": {"login": state.get("user", "agent-user")},
            "comments": [],
        }
        save_state(state_path, state)
        print(f"https://github.com/{repo}/issues/{next_num}")
        return 0

    if sub == "comment":
        num = next((a for a in rest if not a.startswith("-")), "").lstrip("#")
        body = read_body_from_args(rest) or ""
        issue = issues.setdefault(
            num, {"number": int(num) if num.isdigit() else num, "title": "", "body": "", "comments": []}
        )
        cid = 1000 + len(issue.setdefault("comments", [])) + 1
        issue["comments"].append(
            {"id": cid, "author": {"login": state.get("user", "agent-user")}, "body": body}
        )
        save_state(state_path, state)
        print(f"https://github.com/{repo}/issues/{num}#issuecomment-{cid}")
        return 0

    if sub == "edit":
        num = next((a for a in rest if not a.startswith("-")), "").lstrip("#")
        issue = issues.get(num)
        if issue:
            body = read_body_from_args(rest)
            if body is not None:
                issue["body"] = body
            title = extract_flag_value(rest, "--title", "-t")
            if title is not None:
                issue["title"] = title
            save_state(state_path, state)
        print(f"https://github.com/{repo}/issues/{num}")
        return 0

    sys.stderr.write(f"mock-gh: unsupported issue subcommand: {sub}\n")
    return 1


def handle_pr(args: list[str], state: dict[str, Any], state_path: Path) -> int:
    if not args:
        sys.stderr.write("mock-gh: missing pr subcommand\n")
        return 1
    sub, rest = args[0], args[1:]
    repo = extract_flag_value(rest, "-R", "--repo") or state.get("repo", "example/app")
    prs: list[dict[str, Any]] = state.setdefault("prs", [])
    jq_expr = extract_flag_value(rest, "--jq", "-q")
    json_fields = extract_flag_value(rest, "--json")

    def find_pr(num_str: str) -> dict[str, Any] | None:
        n = num_str.lstrip("#")
        for pr in prs:
            if str(pr.get("number")) == n:
                return pr
        return None

    if sub == "list":
        wanted_state = (extract_flag_value(rest, "--state", "-s") or "open").upper()
        search = extract_flag_value(rest, "--search", "-S") or ""
        head = extract_flag_value(rest, "--head", "-H")
        filtered = []
        for pr in prs:
            st = pr.get("state", "OPEN").upper()
            if wanted_state != "ALL" and st != wanted_state:
                continue
            if head and pr.get("headRefName") != head:
                continue
            if search:
                in_body_only = "in:body" in search
                terms = [t for t in search.split() if not t.startswith(("in:", "is:"))]
                haystack = pr.get("body", "") if in_body_only else (pr.get("title", "") + "\n" + pr.get("body", ""))
                if not all(t.lower() in haystack.lower() for t in terms):
                    continue
            filtered.append(pr)
        if json_fields is not None:
            data = [filter_json_fields(pr, json_fields) for pr in filtered]
            print(apply_jq(data, jq_expr))
        else:
            for pr in filtered:
                draft = "DRAFT" if pr.get("isDraft") else pr.get("state", "OPEN")
                print(f"#{pr.get('number')}\t{draft}\t{pr.get('title', '')}\t{pr.get('headRefName', '')}")
        return 0

    if sub == "view":
        num = next((a for a in rest if not a.startswith("-")), "")
        pr = find_pr(num) if num else (prs[0] if prs else None)
        if not pr:
            sys.stderr.write(f"no pull requests found for {num}\n")
            return 1
        if json_fields is not None:
            data = filter_json_fields(pr, json_fields)
            print(apply_jq(data, jq_expr))
        else:
            print(format_pr_view(pr, has_flag(rest, "--comments", "-c")))
        return 0

    if sub == "diff":
        num = next((a for a in rest if not a.startswith("-")), "")
        pr = find_pr(num) if num else (prs[0] if prs else None)
        if not pr:
            sys.stderr.write(f"no pull requests found for {num}\n")
            return 1
        if has_flag(rest, "--name-only"):
            for f in pr.get("diffFiles", []):
                print(f)
        else:
            print(pr.get("diff", "\n".join(f"diff --git a/{f} b/{f}" for f in pr.get("diffFiles", []))))
        return 0

    if sub == "create":
        next_num = max((int(pr.get("number", 0)) for pr in prs), default=200) + 1
        title = extract_flag_value(rest, "--title", "-t") or ""
        body = read_body_from_args(rest) or ""
        is_draft = has_flag(rest, "--draft", "-d")
        head_ref = extract_flag_value(rest, "--head", "-H") or ""
        if not head_ref:
            proc = subprocess.run(["git", "branch", "--show-current"], text=True, capture_output=True, check=False)
            head_ref = proc.stdout.strip()
        prs.append(
            {
                "number": next_num,
                "title": title,
                "body": body,
                "state": "OPEN",
                "isDraft": is_draft,
                "headRefName": head_ref,
                "diffFiles": [],
                "comments": [],
                "reviews": [],
            }
        )
        save_state(state_path, state)
        print(f"https://github.com/{repo}/pull/{next_num}")
        return 0

    if sub == "edit":
        num = next((a for a in rest if not a.startswith("-")), "")
        pr = find_pr(num)
        if pr:
            body = read_body_from_args(rest)
            if body is not None:
                pr["body"] = body
            title = extract_flag_value(rest, "--title", "-t")
            if title is not None:
                pr["title"] = title
            save_state(state_path, state)
        print(f"https://github.com/{repo}/pull/{num}")
        return 0

    if sub == "ready":
        num = next((a for a in rest if not a.startswith("-")), "")
        pr = find_pr(num)
        undo = has_flag(rest, "--undo")
        if pr:
            pr["isDraft"] = undo
            save_state(state_path, state)
        print(f"https://github.com/{repo}/pull/{num}")
        return 0

    if sub == "comment":
        num = next((a for a in rest if not a.startswith("-")), "")
        body = read_body_from_args(rest) or ""
        pr = find_pr(num)
        cid = 2000
        if pr:
            cid = 2000 + len(pr.setdefault("comments", [])) + 1
            pr["comments"].append(
                {"id": cid, "author": {"login": state.get("user", "agent-user")}, "body": body}
            )
            save_state(state_path, state)
        print(f"https://github.com/{repo}/pull/{num}#issuecomment-{cid}")
        return 0

    sys.stderr.write(f"mock-gh: unsupported pr subcommand: {sub}\n")
    return 1


def handle_label(args: list[str], state: dict[str, Any]) -> int:
    if not args or args[0] != "list":
        sys.stderr.write(f"mock-gh: unsupported label subcommand: {args}\n")
        return 1
    rest = args[1:]
    jq_expr = extract_flag_value(rest, "--jq", "-q")
    json_fields = extract_flag_value(rest, "--json")
    labels = [{"name": l} for l in state.get("labels", [])]
    if json_fields is not None:
        print(apply_jq(labels, jq_expr))
    else:
        for l in labels:
            print(l["name"])
    return 0


def handle_api(args: list[str], state: dict[str, Any], state_path: Path) -> int:
    method = (extract_flag_value(args, "-X", "--method") or "GET").upper()
    jq_expr = extract_flag_value(args, "--jq", "-q")
    # Find endpoint (first positional arg not consumed by flags)
    endpoint = ""
    skip_next = False
    flags_with_arg = {"-X", "--method", "--jq", "-q", "-f", "--raw-field", "-F", "--field", "-H", "--header"}
    for a in args:
        if skip_next:
            skip_next = False
            continue
        if a in flags_with_arg:
            skip_next = True
            continue
        if a.startswith("-"):
            continue
        endpoint = a.lstrip("/")
        break

    if endpoint == "user":
        print(apply_jq({"login": state.get("user", "agent-user")}, jq_expr))
        return 0

    m_contents = re.match(r"^repos/([^/]+/[^/]+)/contents/(.+)$", endpoint)
    if m_contents and method == "GET":
        repo_key, rel_path = m_contents.group(1), m_contents.group(2).rstrip("/")
        contents = state.get("repo_contents", {})
        lookup_keys = [f"{repo_key}:{rel_path}", rel_path]
        for key in lookup_keys:
            if key in contents:
                val = contents[key]
                if isinstance(val, list):
                    print(apply_jq([{"name": n} if isinstance(n, str) else n for n in val], jq_expr))
                    return 0
                if isinstance(val, str):
                    encoded = base64.b64encode(val.encode("utf-8")).decode("ascii")
                    print(apply_jq({"name": Path(rel_path).name, "content": encoded, "encoding": "base64"}, jq_expr))
                    return 0
                print(apply_jq(val, jq_expr))
                return 0
        sys.stderr.write(f"gh: Not Found (HTTP 404): {endpoint}\n")
        return 1

    m_patch_comment = re.match(r"^repos/[^/]+/[^/]+/issues/comments/(\d+)$", endpoint)
    if m_patch_comment and method == "PATCH":
        cid = int(m_patch_comment.group(1))
        body = read_body_from_args(args) or ""
        print(apply_jq({"id": cid, "body": body}, jq_expr))
        return 0

    m_pr_comments = re.match(r"^repos/[^/]+/[^/]+/pulls/(\d+)/comments$", endpoint)
    if m_pr_comments and method == "GET":
        num = m_pr_comments.group(1)
        for pr in state.get("prs", []):
            if str(pr.get("number")) == num:
                print(apply_jq(pr.get("reviewComments", []), jq_expr))
                return 0
        print(apply_jq([], jq_expr))
        return 0

    m_reply = re.match(r"^repos/[^/]+/[^/]+/pulls/(\d+)/comments/(\d+)/replies$", endpoint)
    if m_reply:
        body = read_body_from_args(args) or ""
        print(apply_jq({"id": 9001, "body": body}, jq_expr))
        return 0

    print(apply_jq({}, jq_expr))
    return 0


def handle_repo(args: list[str], state: dict[str, Any]) -> int:
    if args and args[0] == "view":
        repo = state.get("repo", "example/app")
        owner, name = repo.split("/", 1) if "/" in repo else ("example", repo)
        data = {
            "nameWithOwner": repo,
            "name": name,
            "owner": {"login": owner},
            "defaultBranchRef": {"name": "main"},
        }
        jq_expr = extract_flag_value(args[1:], "--jq", "-q")
        json_fields = extract_flag_value(args[1:], "--json")
        if json_fields is not None:
            print(apply_jq(filter_json_fields(data, json_fields), jq_expr))
        else:
            print(repo)
        return 0
    return 0


def main() -> int:
    args = sys.argv[1:]
    state_path = Path(os.environ.get("EVAL_GH_STATE", "gh-state.json"))
    log_path = Path(os.environ.get("EVAL_GH_LOG", "gh-calls.jsonl"))
    state = load_state(state_path)

    body = read_body_from_args(args)
    append_log(
        log_path,
        {
            "args": args,
            "command": " ".join(args),
            "body": body,
        },
    )

    if not args:
        print("mock-gh")
        return 0

    cmd, rest = args[0], args[1:]
    if cmd == "issue":
        return handle_issue(rest, state, state_path)
    if cmd == "pr":
        return handle_pr(rest, state, state_path)
    if cmd == "label":
        return handle_label(rest, state)
    if cmd == "api":
        return handle_api(rest, state, state_path)
    if cmd == "repo":
        return handle_repo(rest, state)
    if cmd == "auth":
        print("Logged in to github.com as " + state.get("user", "agent-user"))
        return 0

    sys.stderr.write(f"mock-gh: unsupported command: {cmd}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
