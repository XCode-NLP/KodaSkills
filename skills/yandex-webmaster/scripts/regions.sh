#!/bin/sh
# Regions directory for query analytics
# Usage: regions.sh --host <domain> [--filter "москва"] [--limit N]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config

FILTER=""

_args=""
while [ $# -gt 0 ]; do
    case "$1" in
        --filter) FILTER="$2"; shift 2 ;;
        *)        _args="$_args $1"; shift ;;
    esac
done
# shellcheck disable=SC2086
parse_host_params $_args
ensure_user_id
resolve_host
require_host

TMPFILE="${WM_TMPDIR}/wm_regions_$$.json"
trap 'rm -f "$TMPFILE"' EXIT

_curl_args=""
if [ -n "$FILTER" ]; then
    _curl_args="--data-urlencode filter=$FILTER"
fi
if [ -n "$LIMIT" ]; then
    _curl_args="$_curl_args --data-urlencode limit=$LIMIT"
fi

# PRO endpoint
# shellcheck disable=SC2086
webmaster_raw_get "/v4/user/${USER_ID}/hosts/${HOST_ID}/pro/regions" $_curl_args > "$TMPFILE"

echo "region_id	name"
tr -d '\n\r' < "$TMPFILE" | sed 's/},{/}\n{/g' | while IFS= read -r _line || [ -n "$_line" ]; do
    _rid=$(json_extract_number "$_line" "id")
    [ -z "$_rid" ] && continue
    _rname=$(json_extract_field_raw "$_line" "name")
    printf '%s\t%s\n' "$_rid" "$_rname"
done
