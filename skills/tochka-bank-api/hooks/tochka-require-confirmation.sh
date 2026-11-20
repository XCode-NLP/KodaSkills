#!/bin/bash
# Escalates state-changing Tochka Bank API calls to the built-in
# Claude Code permission prompt (permissionDecision: "ask").
# Read-only calls and non-Tochka commands pass through silently.

set -euo pipefail

input=$(cat)
cmd=$(echo "$input" | jq -r '.tool_input.command // ""')

# Not a Tochka touchpoint — pass through.
if ! echo "$cmd" | grep -qE '(enter\.tochka\.com|tochka_client\.py)'; then
    exit 0
fi

# Decide whether this is a state-changing call.
is_write=no

if echo "$cmd" | grep -qE -- '-X[[:space:]]*(POST|PUT|DELETE|PATCH)'; then
    is_write=yes
fi

if [ "$is_write" = "no" ] && echo "$cmd" | grep -qE 'curl' && echo "$cmd" | grep -qE -- '(-d|--data)[[:space:]]'; then
    is_write=yes
fi

# State-changing helper CLI subcommands (from tochka_client.py argparse).
# Do NOT include "for-sign" here — list-for-sign is read-only and would
# false-positive. Anchored with leading space / start-of-string to avoid
# matching inside option values like --purpose "create-invoice".
if echo "$cmd" | grep -qE '(^|[[:space:]])(create-invoice|send-invoice|create-closing-doc|send-closing-doc|delete-closing-doc|register-webhook|delete-webhook|test-webhook|create-payment-link)([[:space:]]|$)'; then
    is_write=yes
fi

if [ "$is_write" != "yes" ]; then
    exit 0
fi

# Extract the subcommand name from tochka_client.py invocations (empty for raw curl).
# `|| true` keeps the script alive under `set -e` / `pipefail` when grep finds no match.
subcommand=$(echo "$cmd" | grep -oE 'tochka_client\.py[[:space:]]+[a-z][a-z-]+' | awk '{print $2}' | head -1 || true)

# Detect target environment — URL or env-var.
if echo "$cmd" | grep -qE 'sandbox/v2'; then
    target=SANDBOX
elif echo "$cmd" | grep -qE '(^|[[:space:]])TOCHKA_SANDBOX=1'; then
    target=SANDBOX
else
    target=PROD
fi

# Severity wording reflects blast radius.
if [ "$target" = "PROD" ]; then
    severity="real money / bank records may be affected"
else
    severity="sandbox only — no real money / records at risk"
fi

# Header label: "[PROD] create-invoice" or "[SANDBOX]" for raw curl.
if [ -n "$subcommand" ]; then
    label="[$target] $subcommand"
else
    label="[$target]"
fi

preview=$(echo "$cmd" | head -c 400 | tr -d '\000')
reason="Tochka Bank API $label — state-changing call. $severity. Review and confirm:

$preview"

jq -n --arg reason "$reason" '{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "ask",
    "permissionDecisionReason": $reason
  }
}'
