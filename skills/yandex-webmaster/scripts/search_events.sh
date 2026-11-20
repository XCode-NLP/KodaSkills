#!/bin/sh
# Search events — appeared/removed from search
# Usage: search_events.sh --host <domain> --action history|samples
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
TMPFILE="${WM_TMPDIR}/wm_sevents_$$.json"
trap 'rm -f "$TMPFILE"' EXIT

case "$ACTION" in
    history)
        apply_default_dates
        _host_dir=$(cache_host_dir)
        mkdir -p "$_host_dir/insearch"
        _hash=$(cache_key "events_history_${DATE_FROM}_${DATE_TO}")
        _out_file="$_host_dir/insearch/events_${_hash}.tsv"

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
        webmaster_get "/search-urls/events/history" $_curl_args > "$TMPFILE"

        tr -d '\n\r' < "$TMPFILE" > "${TMPFILE}.flat"
        _ta="${WM_TMPDIR}/wm_se_app_$$.tsv"
        _tr="${WM_TMPDIR}/wm_se_rem_$$.tsv"
        trap 'rm -f "$TMPFILE" "${TMPFILE}.flat" "$_ta" "$_tr"' EXIT

        _extract_indicator() {
            grep -o "\"$1\"[[:space:]]*:\[[^]]*\]" "$2" | head -1 | \
                grep -o '"date":"[^"]*","value":[0-9]*' | \
                sed 's/"date":"//;s/","value":/\t/' | cut -c1-10,11- > "$3"
        }
        _extract_indicator "APPEARED_IN_SEARCH" "${TMPFILE}.flat" "$_ta"
        _extract_indicator "REMOVED_FROM_SEARCH" "${TMPFILE}.flat" "$_tr"

        {
            echo "date	appeared	removed"
            _tdates="${WM_TMPDIR}/wm_se_dates_$$.txt"
            cut -f1 "$_ta" "$_tr" | sort -u > "$_tdates"
            awk -F'\t' '
                FILENAME == ARGV[1] { app[$1]=$2; next }
                FILENAME == ARGV[2] { rem[$1]=$2; next }
                {
                    d=$1
                    printf "%s\t%s\t%s\n", d, \
                        (d in app ? app[d] : 0), (d in rem ? rem[d] : 0)
                }
            ' "$_ta" "$_tr" "$_tdates"
            rm -f "$_tdates"
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
        webmaster_get "/search-urls/events/samples" $_curl_args > "$TMPFILE"

        _count=$(json_extract_number "$(cat "$TMPFILE")" "count")

        echo "url	title	event	event_date	excluded_status"
        tr -d '\n\r' < "$TMPFILE" | sed 's/},{/}\n{/g' | while IFS= read -r _line || [ -n "$_line" ]; do
            _url=$(json_extract_field_raw "$_line" "url")
            [ -z "$_url" ] && continue
            _title=$(json_extract_field_raw "$_line" "title")
            _event=$(json_extract_field_raw "$_line" "event")
            _edate=$(json_extract_field_raw "$_line" "event_date")
            _exstatus=$(json_extract_field_raw "$_line" "excluded_url_status")
            _ed=$(printf '%s' "$_edate" | cut -c1-10)
            printf '%s\t%s\t%s\t%s\t%s\n' "$_url" "${_title:--}" "$_event" "${_ed:--}" "${_exstatus:--}"
        done | head -30

        echo ""
        echo "Total events: ${_count:-?} (showing first 30, max 50000 via API)"
        ;;

    *)
        echo "Error: unknown action '$ACTION'. Use: history, samples" >&2
        exit 1
        ;;
esac
