#!/bin/sh
# SQI (Site Quality Index) history
# Usage: sqi_history.sh --host <domain> [--date-from YYYY-MM-DD] [--date-to YYYY-MM-DD]
# Defaults to last 90 days if --date-from is not specified.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config

parse_host_params "$@"
apply_default_dates
ensure_user_id
resolve_host
require_host

TMPFILE="${WM_TMPDIR}/wm_sqi_$$.json"
trap 'rm -f "$TMPFILE"' EXIT

_host_dir=$(cache_host_dir)
_out_file="$_host_dir/sqi_history.tsv"

# TTL cache check (24h)
if [ -z "$NO_CACHE" ] && cache_get_ttl "$_out_file" 1440; then
    print_tsv_head "$_out_file" 30
    echo ""
    echo "(cached: $_out_file)"
    exit 0
fi

# Build curl args for dates
_curl_args=""
if [ -n "$DATE_FROM" ]; then
    _curl_args="$_curl_args --data-urlencode date_from=${DATE_FROM}T00:00:00.000+0300"
fi
if [ -n "$DATE_TO" ]; then
    _curl_args="$_curl_args --data-urlencode date_to=${DATE_TO}T00:00:00.000+0300"
fi

# shellcheck disable=SC2086
webmaster_get "/sqi-history" $_curl_args > "$TMPFILE"

{
    echo "date	sqi"
    tr -d '\n\r' < "$TMPFILE" | grep -o '"date":"[^"]*","value":[0-9]*' | while IFS= read -r _match; do
        _date=$(printf '%s' "$_match" | sed 's/.*"date":"//;s/".*//' | cut -c1-10)
        _val=$(printf '%s' "$_match" | sed 's/.*"value"://')
        printf '%s\t%s\n' "$_date" "$_val"
    done
} > "$_out_file"

print_tsv_head "$_out_file" 30
echo ""
echo "Cached: $_out_file"
