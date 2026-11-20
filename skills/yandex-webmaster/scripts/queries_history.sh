#!/bin/sh
# Search queries history (all or single query)
# Usage: queries_history.sh --host <domain> [--query-id <id>]
#        [--device ALL|DESKTOP|MOBILE_AND_TABLET] [--date-from] [--date-to]
# Defaults to last 90 days if --date-from is not specified.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config

QUERY_ID=""
DEVICE="ALL"

_args=""
while [ $# -gt 0 ]; do
    case "$1" in
        --query-id) QUERY_ID="$2"; shift 2 ;;
        --device)   DEVICE="$2"; shift 2 ;;
        *)          _args="$_args $1"; shift ;;
    esac
done
# shellcheck disable=SC2086
parse_host_params $_args
ensure_user_id
resolve_host
require_host

apply_default_dates

# Cache check before API call
_host_dir=$(cache_host_dir)
mkdir -p "$_host_dir/queries"
_hash=$(cache_key "history_${QUERY_ID}_${DEVICE}_${DATE_FROM}_${DATE_TO}")
_out_file="$_host_dir/queries/history_${_hash}.tsv"

if [ -z "$NO_CACHE" ] && cache_get_ttl "$_out_file" 1440; then
    print_tsv_head "$_out_file" 30
    echo ""
    echo "(cached: $_out_file)"
    exit 0
fi

TMPFILE="${WM_TMPDIR}/wm_qhist_$$.json"
trap 'rm -f "$TMPFILE" "${TMPFILE}.flat"' EXIT

_curl_args="--data-urlencode query_indicator=TOTAL_SHOWS"
_curl_args="$_curl_args --data-urlencode query_indicator=TOTAL_CLICKS"
_curl_args="$_curl_args --data-urlencode query_indicator=AVG_SHOW_POSITION"
_curl_args="$_curl_args --data-urlencode device_type_indicator=$DEVICE"

if [ -n "$DATE_FROM" ]; then
    _curl_args="$_curl_args --data-urlencode date_from=${DATE_FROM}T00:00:00.000+0300"
fi
if [ -n "$DATE_TO" ]; then
    _curl_args="$_curl_args --data-urlencode date_to=${DATE_TO}T00:00:00.000+0300"
fi

if [ -n "$QUERY_ID" ]; then
    # shellcheck disable=SC2086
    webmaster_get "/search-queries/${QUERY_ID}/history" $_curl_args > "$TMPFILE"
else
    # shellcheck disable=SC2086
    webmaster_get "/search-queries/all/history" $_curl_args > "$TMPFILE"
fi

# Flatten, extract indicators to date<TAB>value TSV, merge with awk
tr -d '\n\r' < "$TMPFILE" > "${TMPFILE}.flat"

_ts="${WM_TMPDIR}/wm_qh_shows_$$.tsv"
_tc="${WM_TMPDIR}/wm_qh_clicks_$$.tsv"
_tp="${WM_TMPDIR}/wm_qh_pos_$$.tsv"
trap 'rm -f "$TMPFILE" "${TMPFILE}.flat" "$_ts" "$_tc" "$_tp"' EXIT

_extract_indicator() {
    grep -o "\"$1\"[[:space:]]*:\[[^]]*\]" "$2" | head -1 | \
        grep -o '"date":"[^"]*","value":[0-9.e+-]*' | \
        sed 's/"date":"//;s/","value":/\t/' | cut -c1-10,11- > "$3"
}
_extract_indicator "TOTAL_SHOWS" "${TMPFILE}.flat" "$_ts"
_extract_indicator "TOTAL_CLICKS" "${TMPFILE}.flat" "$_tc"
_extract_indicator "AVG_SHOW_POSITION" "${TMPFILE}.flat" "$_tp"

{
    echo "date	shows	clicks	avg_position"
    _tdates="${WM_TMPDIR}/wm_qh_dates_$$.txt"
    cut -f1 "$_ts" "$_tc" "$_tp" | sort -u > "$_tdates"
    awk -F'\t' '
        FILENAME == ARGV[1] { shows[$1]=$2; next }
        FILENAME == ARGV[2] { clicks[$1]=$2; next }
        FILENAME == ARGV[3] { pos[$1]=$2; next }
        {
            d=$1
            printf "%s\t%s\t%s\t%s\n", d, \
                (d in shows ? shows[d] : 0), \
                (d in clicks ? clicks[d] : 0), \
                (d in pos ? pos[d] : "-")
        }
    ' "$_ts" "$_tc" "$_tp" "$_tdates"
    rm -f "$_tdates"
} > "$_out_file"

print_tsv_head "$_out_file" 30
echo ""
echo "Cached: $_out_file"
