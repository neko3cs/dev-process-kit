#!/usr/bin/env bash
# Run dev-process-kit regression evaluation scenarios in isolated git repos
# with a fixture-driven mock `gh` CLI.
#
# Usage:
#   evals/run.sh --list [--skill <issue|design|implement>]
#   evals/run.sh --harness <claude|codex|copilot> --scenario <id>
#   evals/run.sh --harness <claude|codex|copilot> --skill <issue|design|implement>
#   evals/run.sh --harness <claude|codex|copilot> --all
#   evals/run.sh --setup-only --scenario <id> [--out-dir <dir>]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

HARNESS=""
SCENARIO_ID=""
SKILL_FILTER=""
RUN_ALL=0
SETUP_ONLY=0
LIST_ONLY=0
OUT_DIR=""

usage() {
  sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --list) LIST_ONLY=1; shift ;;
    --harness) [[ $# -ge 2 ]] || { echo "Error: --harness requires a value" >&2; usage >&2; exit 2; }; HARNESS="$2"; shift 2 ;;
    --scenario) [[ $# -ge 2 ]] || { echo "Error: --scenario requires a value" >&2; usage >&2; exit 2; }; SCENARIO_ID="$2"; shift 2 ;;
    --skill) [[ $# -ge 2 ]] || { echo "Error: --skill requires a value" >&2; usage >&2; exit 2; }; SKILL_FILTER="$2"; shift 2 ;;
    --all) RUN_ALL=1; shift ;;
    --setup-only) SETUP_ONLY=1; shift ;;
    --out-dir) [[ $# -ge 2 ]] || { echo "Error: --out-dir requires a value" >&2; usage >&2; exit 2; }; OUT_DIR="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ "$LIST_ONLY" -eq 1 ]]; then
  if [[ -n "$SKILL_FILTER" ]]; then
    python3 "$SCRIPT_DIR/validate.py" --list --skill "$SKILL_FILTER"
  else
    python3 "$SCRIPT_DIR/validate.py" --list
  fi
  exit 0
fi

python3 "$SCRIPT_DIR/validate.py" >/dev/null

if [[ "$SETUP_ONLY" -eq 0 ]]; then
  case "$HARNESS" in
    claude|codex|copilot) ;;
    *)
      echo "Error: specify --harness <claude|codex|copilot> or --setup-only" >&2
      usage >&2
      exit 2
      ;;
  esac
fi

if [[ -z "$SCENARIO_ID" && -z "$SKILL_FILTER" && "$RUN_ALL" -eq 0 ]]; then
  echo "Error: specify one of --scenario <id>, --skill <name>, or --all" >&2
  usage >&2
  exit 2
fi

if [[ -z "$OUT_DIR" ]]; then
  STAMP="$(date +%Y%m%d-%H%M%S)"
  OUT_DIR="${TMPDIR:-/tmp}/dev-process-kit-evals/$STAMP"
fi
mkdir -p "$OUT_DIR"
OUT_DIR="$(cd "$OUT_DIR" && pwd)"

# Resolve selected scenario IDs
SCENARIO_IDS="$(python3 - "$SCRIPT_DIR/scenarios" "$SCENARIO_ID" "$SKILL_FILTER" <<'PY'
import json, sys
from pathlib import Path

scenarios_dir, wanted_id, wanted_skill = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
ids = []
for p in sorted(scenarios_dir.glob("*.json")):
    data = json.loads(p.read_text(encoding="utf-8"))
    skill = data["skill"]
    if wanted_skill and skill != wanted_skill:
        continue
    for sc in data["scenarios"]:
        if wanted_id and sc["id"] != wanted_id:
            continue
        ids.append(f"{skill}\t{sc['id']}")
if not ids:
    sys.exit(1)
print("\n".join(ids))
PY
)" || {
  echo "Error: no matching scenarios found" >&2
  exit 1
}

# Prepare isolated harness homes for codex / copilot once per run
CODEX_TMP_HOME=""
COPILOT_TMP_HOME=""
COPILOT_AUTH_TOKEN=""
if [[ "$SETUP_ONLY" -eq 0 && "$HARNESS" == "codex" ]]; then
  CODEX_TMP_HOME="$OUT_DIR/.codex-home"
  mkdir -p "$CODEX_TMP_HOME"
  SRC_CODEX_AUTH="${CODEX_HOME:-$HOME/.codex}/auth.json"
  if [[ -f "$SRC_CODEX_AUTH" ]]; then
    cp "$SRC_CODEX_AUTH" "$CODEX_TMP_HOME/auth.json"
    chmod 600 "$CODEX_TMP_HOME/auth.json"
  fi
  CODEX_HOME="$CODEX_TMP_HOME" codex plugin marketplace add "$REPO_ROOT" >/dev/null
  CODEX_HOME="$CODEX_TMP_HOME" codex plugin add dev-process-kit@dev-process-kit >/dev/null
elif [[ "$SETUP_ONLY" -eq 0 && "$HARNESS" == "copilot" ]]; then
  COPILOT_TMP_HOME="$OUT_DIR/.copilot-home"
  mkdir -p "$COPILOT_TMP_HOME"
  # Capture real gh auth token before PATH is overridden with mock gh
  if [[ -z "${COPILOT_GITHUB_TOKEN:-}" && -z "${GH_TOKEN:-}" && -z "${GITHUB_TOKEN:-}" ]]; then
    COPILOT_AUTH_TOKEN="$(gh auth token 2>/dev/null || true)"
  fi
  COPILOT_HOME="$COPILOT_TMP_HOME" copilot plugin marketplace add "$REPO_ROOT" >/dev/null
  COPILOT_HOME="$COPILOT_TMP_HOME" copilot plugin install dev-process-kit@dev-process-kit >/dev/null
fi

TOTAL=0
FAILED=0

while IFS=$'\t' read -r -u 3 SKILL SID; do
  SKILL="${SKILL%$'\r'}"
  SID="${SID%$'\r'}"
  TOTAL=$((TOTAL + 1))
  RUN_DIR="$OUT_DIR/$SID"
  mkdir -p "$RUN_DIR/bin" "$RUN_DIR/repo"

  # Set up isolated git repo, remote, branches, and gh fixture state
  PROMPT="$(python3 - "$SCRIPT_DIR/scenarios/$SKILL.json" "$SID" "$RUN_DIR" "$HARNESS" <<'PY'
import json, subprocess, sys
from pathlib import Path

scenario_file, sid, run_dir_s, harness = sys.argv[1:5]
run_dir = Path(run_dir_s)
data = json.loads(Path(scenario_file).read_text(encoding="utf-8"))
skill = data["skill"]
sc = next(s for s in data["scenarios"] if s["id"] == sid)

(run_dir / "scenario.json").write_text(json.dumps(sc, ensure_ascii=False, indent=2), encoding="utf-8")

setup = sc["setup"]
gh_state = setup.get("gh", {})
gh_state.setdefault("repo", "example/app")
gh_state.setdefault("user", "agent-user")
(run_dir / "gh-state.json").write_text(json.dumps(gh_state, ensure_ascii=False, indent=2), encoding="utf-8")
(run_dir / "gh-calls.jsonl").write_text("", encoding="utf-8")

remote = run_dir / "remote.git"
repo = run_dir / "repo"

def git(*args, cwd=repo):
    subprocess.run(["git", *args], cwd=cwd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

subprocess.run(["git", "init", "--bare", "-b", "main", str(remote)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
git("init", "-b", "main")
git("config", "user.name", "Eval User")
git("config", "user.email", "eval@example.com")
git("remote", "add", "origin", str(remote))

files = setup.get("files", {})
if not files:
    files = {"README.md": "# Example App\n"}
for rel, content in files.items():
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

git("add", "-A")
git("commit", "-m", "Initial commit")
git("push", "-u", "origin", "main")

# Optional additional commits on main after branching (e.g., parallel PR merged)
branches = setup.get("branches", {})
for bname, bspec in branches.items():
    base = bspec.get("from", "main")
    git("checkout", "-b", bname, base)
    for rel, content in bspec.get("files", {}).items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    git("add", "-A")
    git("commit", "--allow-empty", "-m", bspec.get("commit_message", f"WIP on {bname}"))
    git("push", "-u", "origin", bname)
    git("checkout", "main")

main_after = setup.get("main_commits_after_branch", [])
for idx, cspec in enumerate(main_after):
    git("checkout", "main")
    for rel, content in cspec.get("files", {}).items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    git("add", "-A")
    git("commit", "--allow-empty", "-m", cspec.get("commit_message", f"Main update {idx + 1}"))
    git("push", "origin", "main")

checkout = setup.get("checkout", "main")
git("checkout", checkout)

# Record initial remote refs and HEAD to detect pushes and edits later
refs = subprocess.check_output(["git", "--git-dir", str(remote), "show-ref"], text=True)
(run_dir / "initial-remote-refs.txt").write_text(refs, encoding="utf-8")
head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
(run_dir / "initial-head.txt").write_text(head_sha, encoding="utf-8")

prefix = "$dev-process-kit:" if harness == "codex" else "/dev-process-kit:"
inv = f"{prefix}{skill}"
args_str = sc["prompt_args"].strip()
print(f"{inv} {args_str}" if args_str else inv)
PY
)"
PROMPT="${PROMPT%$'\r'}"

  cat > "$RUN_DIR/bin/gh" <<EOF
#!/usr/bin/env bash
export EVAL_GH_STATE="$RUN_DIR/gh-state.json"
export EVAL_GH_LOG="$RUN_DIR/gh-calls.jsonl"
exec python3 "$SCRIPT_DIR/lib/mock-gh.py" "\$@"
EOF
  chmod +x "$RUN_DIR/bin/gh"

  # On Windows (Git Bash / MSYS2 / Cygwin), also provide gh.cmd for PowerShell/cmd harnesses
  if command -v cygpath >/dev/null 2>&1; then
    WIN_RUN_DIR="$(cygpath -w "$RUN_DIR")"
    WIN_MOCK_GH="$(cygpath -w "$SCRIPT_DIR/lib/mock-gh.py")"
    cat > "$RUN_DIR/bin/gh.cmd" <<EOF
@echo off
set "EVAL_GH_STATE=$WIN_RUN_DIR\\gh-state.json"
set "EVAL_GH_LOG=$WIN_RUN_DIR\\gh-calls.jsonl"
python3 "$WIN_MOCK_GH" %*
EOF
  fi

  echo "============================================================"
  echo "Scenario: $SID ($SKILL)"
  echo "Workspace: $RUN_DIR/repo"
  echo "Prompt:    $PROMPT"

  if [[ "$SETUP_ONLY" -eq 1 ]]; then
    echo "Mock gh:   PATH=\"$RUN_DIR/bin:\$PATH\""
    continue
  fi

  set +e
  (
    cd "$RUN_DIR/repo"
    export PATH="$RUN_DIR/bin:$PATH"
    case "$HARNESS" in
      claude)
        claude -p \
          --plugin-dir "$REPO_ROOT/plugins/dev-process-kit" \
          --permission-mode bypassPermissions \
          "$PROMPT"
        ;;
      codex)
        CODEX_HOME="$CODEX_TMP_HOME" codex exec \
          --dangerously-bypass-approvals-and-sandbox \
          "$PROMPT"
        ;;
      copilot)
        if [[ -n "$COPILOT_AUTH_TOKEN" ]]; then
          export COPILOT_GITHUB_TOKEN="$COPILOT_AUTH_TOKEN"
        fi
        COPILOT_HOME="$COPILOT_TMP_HOME" copilot \
          -p "$PROMPT" \
          --allow-all-tools \
          --allow-all-paths
        ;;
    esac
  ) < /dev/null > "$RUN_DIR/response.txt" 2> "$RUN_DIR/stderr.txt"
  EXIT_CODE=$?
  set -e

  echo "Exit code: $EXIT_CODE"

  # Evaluate automated checks and print manual review checklist
  if ! python3 - "$RUN_DIR" <<'PY'
import json, re, subprocess, sys
from pathlib import Path

run_dir = Path(sys.argv[1])
sc = json.loads((run_dir / "scenario.json").read_text(encoding="utf-8"))
repo = run_dir / "repo"
remote = run_dir / "remote.git"

calls = []
for line in (run_dir / "gh-calls.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        calls.append(json.loads(line))
commands = [c["command"] for c in calls]

checks = sc["expected"].get("checks", {})
failures = []

for pat in checks.get("gh_must_call", []):
    if not any(re.search(pat, cmd) for cmd in commands):
        failures.append(f"gh_must_call not satisfied: /{pat}/")

for pat in checks.get("gh_must_not_call", []):
    matched = [cmd for cmd in commands if re.search(pat, cmd)]
    if matched:
        failures.append(f"gh_must_not_call violated: /{pat}/ matched {matched}")

if checks.get("git_must_not_push"):
    before = (run_dir / "initial-remote-refs.txt").read_text(encoding="utf-8")
    after = subprocess.check_output(["git", "--git-dir", str(remote), "show-ref"], text=True)
    if before != after:
        failures.append("git_must_not_push violated: remote refs changed")

stay_branch = checks.get("git_branch_must_stay")
if stay_branch:
    cur = subprocess.check_output(["git", "branch", "--show-current"], cwd=repo, text=True).strip()
    if cur != stay_branch:
        failures.append(f"git_branch_must_stay violated: expected {stay_branch!r}, got {cur!r}")

protected = checks.get("git_must_not_modify", [])
if protected:
    initial_head = (run_dir / "initial-head.txt").read_text(encoding="utf-8").strip()
    status_out = subprocess.check_output(["git", "status", "--porcelain", "-uall"], cwd=repo, text=True)
    diff_out = subprocess.check_output(["git", "diff", "--name-only", initial_head, "HEAD"], cwd=repo, text=True)
    touched = set()
    for line in status_out.splitlines():
        if len(line) > 3:
            path_part = line[3:].strip()
            if " -> " in path_part:
                old_p, new_p = path_part.split(" -> ", 1)
                touched.add(old_p.strip().strip('"'))
                touched.add(new_p.strip().strip('"'))
            else:
                touched.add(path_part.strip('"'))
    for line in diff_out.splitlines():
        if line.strip():
            touched.add(line.strip())
    for p in protected:
        if any(t == p or t.startswith(p.rstrip("/") + "/") for t in touched):
            failures.append(f"git_must_not_modify violated: {p}")

print("\nAutomated checks:", "PASS" if not failures else "FAIL")
for f in failures:
    print(f"  - FAIL: {f}")

print(f"\ngh calls ({len(commands)}):")
for cmd in commands:
    print(f"  - gh {cmd}")

print("\nExpected summary:")
print(f"  {sc['expected']['summary']}")
print("Checklist (must):")
for item in sc["expected"]["must"]:
    print(f"  [ ] {item}")
print("Checklist (must not):")
for item in sc["expected"]["must_not"]:
    print(f"  [ ] {item}")
print(f"\nFull response saved to: {run_dir / 'response.txt'}")

sys.exit(1 if failures else 0)
PY
  then
    FAILED=$((FAILED + 1))
  fi
done 3<<< "$SCENARIO_IDS"

echo "============================================================"
echo "Completed $TOTAL scenario(s). Automated check failures: $FAILED"
echo "Artifacts directory: $OUT_DIR"
exit $((FAILED > 0 ? 1 : 0))
