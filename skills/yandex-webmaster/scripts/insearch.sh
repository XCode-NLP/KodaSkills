#!/bin/sh
# Pages in search — history and samples
# Usage: insearch.sh --host <domain> --action history|samples
#        [--date-from] [--date-to] [--limit N] [--offset N]
# History defaults to last 90 days if --date-from is not specified.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config

parse_host_params "$@"
ensure_user_id
resolve_host
require_host

ACTION="${ACTION:-history}"
TMPFILE="${WM_TMPDIR}/wm_insearch_$$.json"
trap 'rm -f "$TMPFILE"' EXIT

case "$ACTION" in
    history)
        apply_default_dates
        _host_dir=$(cache_host_dir)
        mkdir -p "$_host_dir/insearch"
        _hash=$(cache_key "insearch_history_${DATE_FROM}_${DATE_TO}")
        _out_file="$_host_dir/insearch/history_${_hash}.tsv"

        # TTL cache check (24h)
        if [ -z "$NO_CACHE" ] && cache_get_ttl "$_out_file" 1440; then
            print_tsv_head "$_out_file" 30
            echo ""
            echo "(cached: $_out_file)"
            exit 0
        fi

        _curl_args=""
        if [ -n "$DATE_FROM" ]; then
            _curl_args="--data-urlencode date_from=${DATE_FROM}T00:00:00.000+0300"
        fi
        if [ -n "$DATE_TO" ]; then
            _curl_args="$_curl_args --data-urlencode date_to=${DATE_TO}T00:00:00.000+0300"
        fi

        # shellcheck disable=SC2086
        webmaster_get "/search-urls/in-search/history" $_curl_args > "$TMPFILE"

        {
            echo "date	pages_in_search"
            tr -d '\n\r' < "$TMPFILE" | grep -o '"date":"[^"]*","value":[0-9]*' | while IFS= read -r _match; do
                _date=$(printf '%s' "$_match" | sed 's/.*"date":"//;s/".*//' | cut -c1-10)
                _val=$(printf '%s' "$_match" | sed 's/.*"value"://')
                printf '%s\t%s\n' "$_date" "$_val"
            done
        } > "$_out_file"

        print_tsv_head "$_out_file" 30
        echo ""
        echo "Cached: $_out_file"
        ;;

    samples)
        _curl_args=""
        if [ -n "$LIMIT" ]; then
            _curl_args="--data-urlencode limit=$LIMIT"
        fi
        if [ -n "$OFFSET" ]; then
            _curl_args="$_curl_args --data-urlencode offset=$OFFSET"
        fi

        # shellcheck disable=SC2086
        webmaster_get "/search-urls/in-search/samples" $_curl_args > "$TMPFILE"

        _count=$(json_extract_number "$(cat "$TMPFILE")" "count")

        echo "url	title	last_access"
        tr -d '\n\r' < "$TMPFILE" | sed 's/},{/}\n{/g' | while IFS= read -r _line || [ -n "$_line" ]; do
            _url=$(json_extract_field_raw "$_line" "url")
            [ -z "$_url" ] && continue
            _title=$(json_extract_field_raw "$_line" "title")
            _access=$(json_extract_field_raw "$_line" "last_access")
            _adate=$(printf '%s' "$_access" | cut -c1-10)
            printf '%s\t%s\t%s\n' "$_url" "${_title:--}" "${_adate:--}"
        done | head -30

        echo ""
        echo "Total in search: ${_count:-?} (showing first 30, max 50000 via API)"
        ;;

    *)
        echo "Error: unknown action '$ACTION'. Use: history, samples" >&2
        exit 1
        ;;
esac
