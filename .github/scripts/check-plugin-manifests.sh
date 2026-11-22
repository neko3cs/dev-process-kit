#!/usr/bin/env bash
# Checks that the plugin manifests and the marketplace files agree.
#
# Usage: .github/scripts/check-plugin-manifests.sh [<base-ref>]
#   With <base-ref> (for example origin/main), also warns when files under
#   plugins/ changed since <base-ref> but the plugin version did not.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

marketplaces=(
  .claude-plugin/marketplace.json
  .agents/plugins/marketplace.json
  .github/plugin/marketplace.json
)

base="${1:-}"
if [[ -n "$base" ]] && ! git rev-parse --verify --quiet "$base^{commit}" >/dev/null; then
  echo "::error::base ref '$base' not found"
  exit 1
fi

errors=0
fail() {
  echo "::error::$*"
  errors=$((errors + 1))
}

# The plugin directory an entry points to. Claude Code and Copilot CLI use a
# string; Codex uses {"source": "local", "path": ...}.
entry_dirs() {
  jq -r '.plugins[]
    | (if (.source | type) == "string" then .source else .source.path end) as $path
    | "\(.name)\t\($path | ltrimstr("./") | rtrimstr("/"))"' "$1" | sort
}

reference="${marketplaces[0]}"
expected="$(entry_dirs "$reference")"
for mp in "${marketplaces[@]}"; do
  actual="$(entry_dirs "$mp")"
  if [[ "$actual" != "$expected" ]]; then
    fail "$mp: plugin entries (name and source) differ from $reference"
    printf '  %s:\n%s\n  %s:\n%s\n' "$reference" "$expected" "$mp" "$actual"
  fi
  for name in $(jq -r '.plugins[] | select(has("version")) | .name' "$mp"); do
    fail "$mp: entry '$name' sets version; set it only in plugin.json"
  done
done

# Each plugin's three manifests must share name and version.
while IFS=$'\t' read -r name dir; do
  manifests=(
    "$dir/.claude-plugin/plugin.json"
    "$dir/.codex-plugin/plugin.json"
    "$dir/plugin.json"
  )
  versions=()
  for m in "${manifests[@]}"; do
    if [[ ! -f "$m" ]]; then
      fail "$m: missing"
      continue
    fi
    [[ "$(jq -r '.name' "$m")" == "$name" ]] || fail "$m: name is not '$name'"
    versions+=("$(jq -r '.version // "(none)"' "$m")")
  done
  if [[ "$(printf '%s\n' "${versions[@]}" | sort -u | wc -l)" -ne 1 ]]; then
    fail "$name: version differs across manifests: ${versions[*]}"
  fi

  if [[ -n "$base" ]]; then
    if [[ -n "$(git diff --name-only "$base"...HEAD -- "$dir")" ]]; then
      old="$(git show "$base:$dir/.claude-plugin/plugin.json" 2>/dev/null | jq -r '.version' || echo "")"
      if [[ "$old" == "${versions[0]}" ]]; then
        echo "::warning::$name: files under $dir changed but version is still $old; bump it if this is a release"
      fi
    fi
  fi
done <<< "$expected"

if [[ $errors -gt 0 ]]; then
  echo "$errors problem(s) found"
  exit 1
fi
echo "Plugin manifests and marketplaces agree"
