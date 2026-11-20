#!/bin/sh
# Site diagnostics — list all problems with severity and state
# Usage: diagnostics.sh --host <domain>
# NOT cached (always live data)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config

parse_host_params "$@"
ensure_user_id
resolve_host
require_host

TMPFILE="${WM_TMPDIR}/wm_diag_$$.json"
trap 'rm -f "$TMPFILE"' EXIT

webmaster_get "/diagnostics" > "$TMPFILE"

echo "problem	severity	state	last_update"

# Parse each problem entry
tr -d '\n\r' < "$TMPFILE" | sed 's/"problems"[[:space:]]*:{//;s/}[[:space:]]*$//' | \
    grep -o '"[A-Z_]*"[[:space:]]*:{[^}]*}' | while IFS= read -r _entry; do
    _name=$(printf '%s' "$_entry" | grep -o '^"[^"]*"' | sed 's/"//g')
    _severity=$(json_extract_field_raw "$_entry" "severity")
    _state=$(json_extract_field_raw "$_entry" "state")
    _updated=$(json_extract_field_raw "$_entry" "last_state_update")
    _date=$(printf '%s' "$_updated" | cut -c1-10)
    printf '%s\t%s\t%s\t%s\n' "$_name" "$_severity" "$_state" "${_date:--}"
done
