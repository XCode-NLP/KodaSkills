#!/bin/sh
# Indexing history and samples
# Usage: indexing.sh --host <domain> --action history|samples
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
TMPFILE="${WM_TMPDIR}/wm_indexing_$$.json"
trap 'rm -f "$TMPFILE"' EXIT

case "$ACTION" in
    history)
        apply_default_dates
        _host_dir=$(cache_host_dir)
        mkdir -p "$_host_dir/indexing"
        _hash=$(cache_key "indexing_history_${DATE_FROM}_${DATE_TO}")
        _out_file="$_host_dir/indexing/history_${_hash}.tsv"

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
        webmaster_get "/indexing/history" $_curl_args > "$TMPFILE"

        # Flatten JSON, extract each indicator to date<TAB>value TSV, merge with awk
        tr -d '\n\r' < "$TMPFILE" > "${TMPFILE}.flat"

        _t2="${WM_TMPDIR}/wm_idx_2xx_$$.tsv"
        _t3="${WM_TMPDIR}/wm_idx_3xx_$$.tsv"
        _t4="${WM_TMPDIR}/wm_idx_4xx_$$.tsv"
        _t5="${WM_TMPDIR}/wm_idx_5xx_$$.tsv"
        _to="${WM_TMPDIR}/wm_idx_oth_$$.tsv"
        trap 'rm -f "$TMPFILE" "${TMPFILE}.flat" "$_t2" "$_t3" "$_t4" "$_t5" "$_to"' EXIT

        # Extract date<TAB>value for each indicator (one grep + sed per indicator)
        _extract_indicator() {
            grep -o "\"$1\"[[:space:]]*:\[[^]]*\]" "$2" | head -1 | \
                grep -o '"date":"[^"]*","value":[0-9]*' | \
                sed 's/"date":"//;s/","value":/\t/' | cut -c1-10,11- > "$3"
        }
        _extract_indicator "HTTP_2XX" "${TMPFILE}.flat" "$_t2"
        _extract_indicator "HTTP_3XX" "${TMPFILE}.flat" "$_t3"
        _extract_indicator "HTTP_4XX" "${TMPFILE}.flat" "$_t4"
        _extract_indicator "HTTP_5XX" "${TMPFILE}.flat" "$_t5"
        _extract_indicator "OTHER" "${TMPFILE}.flat" "$_to"

        # Merge all indicators by date: sorted date list + awk lookup (O(n), portable)
        _tdates="${WM_TMPDIR}/wm_idx_dates_$$.txt"
        cut -f1 "$_t2" "$_t3" "$_t4" "$_t5" "$_to" | sort -u > "$_tdates"

        {
            echo "date	2xx	3xx	4xx	5xx	other"
            awk -F'\t' '
                FILENAME == ARGV[1] { v2[$1]=$2; next }
                FILENAME == ARGV[2] { v3[$1]=$2; next }
                FILENAME == ARGV[3] { v4[$1]=$2; next }
                FILENAME == ARGV[4] { v5[$1]=$2; next }
                FILENAME == ARGV[5] { vo[$1]=$2; next }
                {
                    d=$1
                    printf "%s\t%s\t%s\t%s\t%s\t%s\n", d, \
                        (d in v2 ? v2[d] : 0), (d in v3 ? v3[d] : 0), \
                        (d in v4 ? v4[d] : 0), (d in v5 ? v5[d] : 0), \
                        (d in vo ? vo[d] : 0)
                }
            ' "$_t2" "$_t3" "$_t4" "$_t5" "$_to" "$_tdates"
        } > "$_out_file"
        rm -f "$_tdates"

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
        webmaster_get "/indexing/samples" $_curl_args > "$TMPFILE"

        _count=$(json_extract_number "$(cat "$TMPFILE")" "count")

        echo "url	status	http_code	access_date"
        tr -d '\n\r' < "$TMPFILE" | sed 's/},{/}\n{/g' | while IFS= read -r _line || [ -n "$_line" ]; do
            _url=$(json_extract_field_raw "$_line" "url")
            [ -z "$_url" ] && continue
            _status=$(json_extract_field_raw "$_line" "status")
            _code=$(json_extract_number "$_line" "http_code")
            _access=$(json_extract_field_raw "$_line" "access_date")
            _adate=$(printf '%s' "$_access" | cut -c1-10)
            printf '%s\t%s\t%s\t%s\n' "$_url" "$_status" "${_code:--}" "${_adate:--}"
        done | head -30

        echo ""
        echo "Total URLs: ${_count:-?} (showing first 30, max 50000 via API)"
        ;;

    *)
        echo "Error: unknown action '$ACTION'. Use: history, samples" >&2
        exit 1
        ;;
esac
