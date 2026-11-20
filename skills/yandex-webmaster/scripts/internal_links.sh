#!/bin/sh
# Broken internal links — samples and history
# Usage: internal_links.sh --host <domain> --action samples|history
#        [--indicator SITE_ERROR|DISALLOWED_BY_USER|UNSUPPORTED_BY_ROBOT]
#        [--date-from] [--date-to] [--limit N] [--offset N]
# History defaults to last 90 days if --date-from is not specified.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config

INDICATOR=""

_args=""
while [ $# -gt 0 ]; do
    case "$1" in
        --indicator) INDICATOR="$2"; shift 2 ;;
        *)           _args="$_args $1"; shift ;;
    esac
done
# shellcheck disable=SC2086
parse_host_params $_args
ensure_user_id
resolve_host
require_host

ACTION="${ACTION:-samples}"
TMPFILE="${WM_TMPDIR}/wm_intlinks_$$.json"
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
        if [ -n "$INDICATOR" ]; then
            _curl_args="$_curl_args --data-urlencode indicator=$INDICATOR"
        fi

        # shellcheck disable=SC2086
        webmaster_get "/links/internal/broken/samples" $_curl_args > "$TMPFILE"

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
        echo "Total broken links: ${_count:-?} (showing first 30)"
        ;;

    history)
        apply_default_dates
        _host_dir=$(cache_host_dir)
        mkdir -p "$_host_dir/links"
        _hash=$(cache_key "int_links_history_${DATE_FROM}_${DATE_TO}")
        _out_file="$_host_dir/links/internal_history_${_hash}.tsv"

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
        webmaster_get "/links/internal/broken/history" $_curl_args > "$TMPFILE"

        tr -d '\n\r' < "$TMPFILE" > "${TMPFILE}.flat"
        _tdbu="${WM_TMPDIR}/wm_il_dbu_$$.tsv"
        _tse="${WM_TMPDIR}/wm_il_se_$$.tsv"
        _tubr="${WM_TMPDIR}/wm_il_ubr_$$.tsv"
        trap 'rm -f "$TMPFILE" "${TMPFILE}.flat" "$_tdbu" "$_tse" "$_tubr"' EXIT

        _extract_indicator() {
            grep -o "\"$1\"[[:space:]]*:\[[^]]*\]" "$2" | head -1 | \
                grep -o '"date":"[^"]*","value":[0-9]*' | \
                sed 's/"date":"//;s/","value":/\t/' | cut -c1-10,11- > "$3"
        }
        _extract_indicator "SITE_ERROR" "${TMPFILE}.flat" "$_tse"
        _extract_indicator "DISALLOWED_BY_USER" "${TMPFILE}.flat" "$_tdbu"
        _extract_indicator "UNSUPPORTED_BY_ROBOT" "${TMPFILE}.flat" "$_tubr"

        {
            echo "date	site_error	disallowed_by_user	unsupported_by_robot"
            _tdates="${WM_TMPDIR}/wm_il_dates_$$.txt"
            cut -f1 "$_tse" "$_tdbu" "$_tubr" | sort -u > "$_tdates"
            awk -F'\t' '
                FILENAME == ARGV[1] { se[$1]=$2; next }
                FILENAME == ARGV[2] { dbu[$1]=$2; next }
                FILENAME == ARGV[3] { ubr[$1]=$2; next }
                {
                    d=$1
                    printf "%s\t%s\t%s\t%s\n", d, \
                        (d in se ? se[d] : 0), (d in dbu ? dbu[d] : 0), \
                        (d in ubr ? ubr[d] : 0)
                }
            ' "$_tse" "$_tdbu" "$_tubr" "$_tdates"
            rm -f "$_tdates"
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
