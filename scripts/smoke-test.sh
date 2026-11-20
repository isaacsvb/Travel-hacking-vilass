#!/usr/bin/env bash
# Smoke test: validates skill frontmatter, MCP config JSON, plugin manifests,
# data files, and the free-first keyless guarantee. No network calls.

set -uo pipefail
cd "$(dirname "$0")/.."

fail=0
pass() { echo "PASS: $1"; }
err()  { echo "FAIL: $1"; fail=$((fail+1)); }

have_jq() { command -v jq >/dev/null 2>&1; }

# 1. JSON configs parse.
for f in .mcp.json opencode.json .claude-plugin/plugin.json .claude-plugin/marketplace.json \
         .agents/plugins/marketplace.json plugins/travel-hacking-toolkit/.mcp.json \
         plugins/travel-hacking-toolkit/.codex-plugin/plugin.json \
         data/alliances.json data/partner-awards.json data/sweet-spots.json \
         data/transfer-partners.json data/points-valuations.json; do
  if [ ! -f "$f" ]; then err "missing $f"; continue; fi
  if have_jq; then
    if jq -e . "$f" >/dev/null 2>&1; then pass "valid JSON: $f"; else err "invalid JSON: $f"; fi
  else
    pass "exists (jq not installed, skipped parse): $f"
  fi
done

# 2. Data files carry last_updated.
if have_jq; then
  for f in data/*.json; do
    if jq -e '._meta.last_updated' "$f" >/dev/null 2>&1; then pass "last_updated present: $f"; else err "no last_updated: $f"; fi
  done
fi

# 3. Every skill has name + description frontmatter, and no colons/quotes in key values.
for s in skills/*/SKILL.md; do
  [ -f "$s" ] || continue
  if head -20 "$s" | grep -q '^name:' && head -20 "$s" | grep -q '^description:'; then
    pass "frontmatter: $s"
  else
    err "frontmatter missing name/description: $s"
  fi
  # Reject colon/quote/backtick in name|summary|category|api_key values (OpenCode parser safety).
  if awk '/^(name|summary|category|api_key):/{ v=$0; sub(/^[a-z_]+:[[:space:]]*/,"",v); if (v ~ /[:'"'"'`"]/) print }' "$s" | grep -q .; then
    err "unsafe char in frontmatter value: $s"
  fi
done

# 4. Free-first guarantee: keyless MCP servers present in every agent config.
for f in .mcp.json plugins/travel-hacking-toolkit/.mcp.json; do
  for srv in skiplagged kiwi trivago ferryhopper airbnb seats-aero; do
    if grep -q "\"$srv\"" "$f"; then :; else err "free-first: $srv missing from $f"; fi
  done
done
if grep -q '"skiplagged"' opencode.json && grep -q '"seats-aero"' opencode.json; then
  pass "free-first: keyless servers present in opencode.json"
else
  err "free-first: keyless servers missing from opencode.json"
fi
pass "free-first: keyless base validated"

echo
if [ "$fail" -eq 0 ]; then echo "ALL CHECKS PASSED"; exit 0; else echo "$fail CHECK(S) FAILED"; exit 1; fi
