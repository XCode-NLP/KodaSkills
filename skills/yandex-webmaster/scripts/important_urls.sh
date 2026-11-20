#!/bin/sh
# Important URLs — list and history
# Usage: important_urls.sh --host <domain> --action list|history [--url URL_FOR_HISTORY]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config

PAGE_URL=""

_args=""
while [ $# -gt 0 ]; do
    case "$1" in
        --url) PAGE_URL="$2"; shift 2 ;;
        *)     _args="$_args $1"; shift ;;
    esac
done
# shellcheck disable=SC2086
parse_host_params $_args
ensure_user_id
resolve_host
require_host

ACTION="${ACTION:-list}"
TMPFILE="${WM_TMPDIR}/wm_impurls_$$.json"
trap 'rm -f "$TMPFILE"' EXIT

case "$ACTION" in
    list)
        webmaster_get "/important-urls" > "$TMPFILE"

        echo "url	indexing_status	http_code	searchable	title	changes"
        tr -d '\n\r' < "$TMPFILE" | sed 's/},{/}\n{/g' | while IFS= read -r _line || [ -n "$_line" ]; do
            _url=$(json_extract_field_raw "$_line" "url")
            [ -z "$_url" ] && continue
            _istatus=$(json_extract_field_raw "$_line" "status")
            _icode=$(json_extract_number "$_line" "http_code")
            _searchable=$(json_extract_bool "$_line" "searchable")
            _title=$(json_extract_field_raw "$_line" "title")
            _changes=$(json_extract_array_strings "$_line" "change_indicators" | tr '\n' ',' | sed 's/,$//')
            printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$_url" "${_istatus:--}" "${_icode:--}" "${_searchable:--}" "${_title:--}" "${_changes:--}"
        done
        ;;

    history)
        if [ -z "$PAGE_URL" ]; then
            echo "Error: --url <page_url> is required for --action history" >&2
            exit 1
        fi
        webmaster_get "/important-urls/history" --data-urlencode "url=$PAGE_URL" > "$TMPFILE"

        echo "update_date	indexing_status	http_code	searchable	title"
        tr -d '\n\r' < "$TMPFILE" | sed 's/},{/}\n{/g' | while IFS= read -r _line || [ -n "$_line" ]; do
            _udate=$(json_extract_field_raw "$_line" "update_date")
            [ -z "$_udate" ] && continue
            _istatus=$(json_extract_field_raw "$_line" "status")
            _icode=$(json_extract_number "$_line" "http_code")
            _searchable=$(json_extract_bool "$_line" "searchable")
            _title=$(json_extract_field_raw "$_line" "title")
            _date=$(printf '%s' "$_udate" | cut -c1-10)
            printf '%s\t%s\t%s\t%s\t%s\n' "$_date" "${_istatus:--}" "${_icode:--}" "${_searchable:--}" "${_title:--}"
        done
        ;;

    *)
        echo "Error: unknown action '$ACTION'. Use: list, history" >&2
        exit 1
        ;;
esac
