#!/usr/bin/env bash
# Travel Hacking Toolkit - optional API key setup.
# All keys are OPTIONAL. The toolkit is free-first: it works with none of them.
# This script prompts for each optional key with masked input, validates it,
# writes it to your shell rc with a backup, and never echoes the value back.

set -euo pipefail

# Keys: VAR_NAME|description|min_length
KEYS=(
  "SEATS_AERO_API_KEY|seats.aero Pro (live award search, >60 days, alerts)|8"
  "DUFFEL_API_KEY|Duffel (cleaner per-fare-class cash pricing)|8"
  "AWARDWALLET_API_KEY|AwardWallet (auto-pull balances)|8"
  "AWARDWALLET_USER_ID|AwardWallet user id|1"
  "LITEAPI_API_KEY|LiteAPI (live hotel rates)|8"
)

# Pick the shell rc.
detect_rc() {
  case "${SHELL:-}" in
    *zsh) echo "$HOME/.zshrc" ;;
    *bash) echo "$HOME/.bashrc" ;;
    *) echo "$HOME/.profile" ;;
  esac
}

RC="$(detect_rc)"
echo "Travel Hacking Toolkit - optional key setup"
echo "Every key is optional. Press Enter to skip any of them."
echo "Keys will be written to: $RC"
echo

[ -f "$RC" ] && cp "$RC" "$RC.bak.$(date +%s)" && echo "Backed up $RC"

for entry in "${KEYS[@]}"; do
  IFS='|' read -r var desc minlen <<< "$entry"
  printf "%s\n  %s: " "$desc" "$var"
  # Masked input.
  stty -echo 2>/dev/null || true
  read -r value
  stty echo 2>/dev/null || true
  echo

  [ -z "$value" ] && { echo "  skipped"; continue; }

  # Validate: reject single quotes (would break the export) and enforce min length.
  if printf '%s' "$value" | grep -q "'"; then
    echo "  rejected: value contains a single quote"; continue
  fi
  if [ "${#value}" -lt "$minlen" ]; then
    echo "  rejected: shorter than $minlen characters"; continue
  fi

  # Remove any prior export of this var, then append. Single-quote to neutralize metacharacters.
  if [ -f "$RC" ]; then
    grep -v "^export $var=" "$RC" > "$RC.tmp" && mv "$RC.tmp" "$RC"
  fi
  printf "export %s='%s'\n" "$var" "$value" >> "$RC"
  echo "  saved"
done

echo
echo "Done. Open a new terminal or run: source $RC"
echo "The toolkit already works without any of these keys."
