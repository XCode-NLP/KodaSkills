#!/bin/sh
# Site summary: SQI, page counts, problems
# Usage: summary.sh --host <domain>

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config

parse_host_params "$@"
ensure_user_id
resolve_host
require_host

TMPFILE="${WM_TMPDIR}/wm_summary_$$.json"
trap 'rm -f "$TMPFILE"' EXIT

webmaster_get "/summary" > "$TMPFILE"
_body=$(cat "$TMPFILE")

_sqi=$(json_extract_number "$_body" "sqi")
_searchable=$(json_extract_number "$_body" "searchable_pages_count")
_excluded=$(json_extract_number "$_body" "excluded_pages_count")

echo "=== Site Summary ==="
echo "SQI:              ${_sqi:-0}"
echo "Searchable pages: ${_searchable:-0}"
echo "Excluded pages:   ${_excluded:-0}"

echo ""
echo "=== Site Problems ==="
_fatal=$(printf '%s' "$_body" | grep -o '"FATAL"[[:space:]]*:[[:space:]]*[0-9]*' | head -1 | sed 's/.*:[[:space:]]*//')
_critical=$(printf '%s' "$_body" | grep -o '"CRITICAL"[[:space:]]*:[[:space:]]*[0-9]*' | head -1 | sed 's/.*:[[:space:]]*//')
_possible=$(printf '%s' "$_body" | grep -o '"POSSIBLE_PROBLEM"[[:space:]]*:[[:space:]]*[0-9]*' | head -1 | sed 's/.*:[[:space:]]*//')
_recommend=$(printf '%s' "$_body" | grep -o '"RECOMMENDATION"[[:space:]]*:[[:space:]]*[0-9]*' | head -1 | sed 's/.*:[[:space:]]*//')

echo "FATAL:            ${_fatal:-0}"
echo "CRITICAL:         ${_critical:-0}"
echo "POSSIBLE_PROBLEM: ${_possible:-0}"
echo "RECOMMENDATION:   ${_recommend:-0}"

if [ "${_fatal:-0}" -gt 0 ] 2>/dev/null || [ "${_critical:-0}" -gt 0 ] 2>/dev/null; then
    echo ""
    echo "Run 'bash scripts/diagnostics.sh --host ...' for details."
fi
