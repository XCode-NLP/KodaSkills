#!/bin/sh
# External links — samples and history
# Usage: external_links.sh --host <domain> --action samples|history
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

ACTION="${ACTION:-samples}"
TMPFILE="${WM_TMPDIR}/wm_extlinks_$$.json"
trap 'rm -f "$TMPFILE"' EXIT

case "$ACTION" in
    samples)
        _curl_args=""
        if [ -n "$LIMIT" ]; then
            _curl_args="--data-urlencode limit=$LIMIT"
        fi
        if [ -n "$OFFSET" ]; then
            _curl_args="$_curl_args --data-urlencode offset=$OFFSET"
        fi

        # shellcheck disable=SC2086
        webmaster_get "/links/external/samples" $_curl_args > "$TMPFILE"

        _count=$(json_extract_number "$(cat "$TMPFILE")" "count")

        echo "source_url	destination_url	discovery_date"
        tr -d '\n\r' < "$TMPFILE" | sed 's/},{/}\n{/g' | while IFS= read -r _line || [ -n "$_line" ]; do
            _src=$(json_extract_field_raw "$_line" "source_url")
            [ -z "$_src" ] && continue
            _dst=$(json_extract_field_raw "$_line" "destination_url")
            _disc=$(json_extract_field_raw "$_line" "discovery_date")
            printf '%s\t%s\t%s\n' "$_src" "$_dst" "${_disc:--}"
        done | head -30

        echo ""
        echo "Total external links: ${_count:-?} (showing first 30)"
        ;;

    history)
        apply_default_dates
        _host_dir=$(cache_host_dir)
        mkdir -p "$_host_dir/links"
        _hash=$(cache_key "ext_links_history_${DATE_FROM}_${DATE_TO}")
        _out_file="$_host_dir/links/external_history_${_hash}.tsv"

        # TTL cache check (24h)
        if [ -z "$NO_CACHE" ] && cache_get_ttl "$_out_file" 1440; then
            print_tsv_head "$_out_file" 30
            echo ""
            echo "(cached: $_out_file)"
            exit 0
        fi

        _curl_args="--data-urlencode indicator=LINKS_TOTAL_COUNT"
        if [ -n "$DATE_FROM" ]; then
            _curl_args="$_curl_args --data-urlencode date_from=${DATE_FROM}T00:00:00.000+0300"
        fi
        if [ -n "$DATE_TO" ]; then
            _curl_args="$_curl_args --data-urlencode date_to=${DATE_TO}T00:00:00.000+0300"
        fi

        # shellcheck disable=SC2086
        webmaster_get "/links/external/history" $_curl_args > "$TMPFILE"

        {
            echo "date	total_links"
            tr -d '\n\r' < "$TMPFILE" | grep -o '"date":"[^"]*","value":"[^"]*"' | while IFS= read -r _match; do
                _date=$(printf '%s' "$_match" | sed 's/.*"date":"//;s/".*//' | cut -c1-10)
                _val=$(printf '%s' "$_match" | grep -o '"value":"[^"]*"' | sed 's/"value":"//;s/"$//')
                printf '%s\t%s\n' "$_date" "$_val"
            done
        } > "$_out_file"

        print_tsv_head "$_out_file" 30
        echo ""
        echo "Cached: $_out_file"
        ;;

    *)
        echo "Error: unknown action '$ACTION'. Use: samples, history" >&2
        exit 1
        ;;
esac
