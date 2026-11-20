#!/bin/sh
# URL recrawl — submit, status, list, quota
# Usage: recrawl.sh --host <domain> --action submit|status|list|quota
#        [--url URL] [--task-id ID] [--date-from] [--date-to] [--limit N] [--offset N]
# NOT cached (always live data)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config

RECRAWL_URL=""
TASK_ID=""

_args=""
while [ $# -gt 0 ]; do
    case "$1" in
        --url)     RECRAWL_URL="$2"; shift 2 ;;
        --task-id) TASK_ID="$2"; shift 2 ;;
        *)         _args="$_args $1"; shift ;;
    esac
done
# shellcheck disable=SC2086
parse_host_params $_args
ensure_user_id
resolve_host
require_host

ACTION="${ACTION:-quota}"
TMPFILE="${WM_TMPDIR}/wm_recrawl_$$.json"
trap 'rm -f "$TMPFILE"' EXIT

case "$ACTION" in
    submit)
        if [ -z "$RECRAWL_URL" ]; then
            echo "Error: --url <page_url> is required for --action submit" >&2
            exit 1
        fi
        _escaped_url=$(json_escape "$RECRAWL_URL")
        webmaster_post "/recrawl/queue" "{\"url\":\"$_escaped_url\"}" > "$TMPFILE"
        _body=$(cat "$TMPFILE")
        _tid=$(json_extract_field_raw "$_body" "task_id")
        _quota=$(json_extract_number "$_body" "quota_remainder")
        echo "URL submitted for recrawl."
        echo "Task ID:         $_tid"
        echo "Quota remaining: ${_quota:-?}"
        ;;

    status)
        if [ -z "$TASK_ID" ]; then
            echo "Error: --task-id is required for --action status" >&2
            exit 1
        fi
        webmaster_get "/recrawl/queue/${TASK_ID}" > "$TMPFILE"
        _body=$(cat "$TMPFILE")
        echo "=== Recrawl Task ==="
        echo "Task ID: $(json_extract_field_raw "$_body" "task_id")"
        echo "URL:     $(json_extract_field_raw "$_body" "url")"
        echo "State:   $(json_extract_field_raw "$_body" "state")"
        echo "Added:   $(json_extract_field_raw "$_body" "added_time")"
        ;;

    list)
        _curl_args=""
        if [ -n "$LIMIT" ]; then
            _curl_args="--data-urlencode limit=$LIMIT"
        fi
        if [ -n "$OFFSET" ]; then
            _curl_args="$_curl_args --data-urlencode offset=$OFFSET"
        fi
        if [ -n "$DATE_FROM" ]; then
            _curl_args="$_curl_args --data-urlencode date_from=${DATE_FROM}T00:00:00.000+0300"
        fi
        if [ -n "$DATE_TO" ]; then
            _curl_args="$_curl_args --data-urlencode date_to=${DATE_TO}T00:00:00.000+0300"
        fi

        # shellcheck disable=SC2086
        webmaster_get "/recrawl/queue" $_curl_args > "$TMPFILE"

        _list_tmp="${WM_TMPDIR}/wm_recrawl_list_$$.tsv"
        {
            echo "task_id	url	state	added_time"
            tr -d '\n\r' < "$TMPFILE" | sed 's/},{/}\n{/g' | while IFS= read -r _line || [ -n "$_line" ]; do
                _tid=$(json_extract_field_raw "$_line" "task_id")
                [ -z "$_tid" ] && continue
                _url=$(json_extract_field_raw "$_line" "url")
                _state=$(json_extract_field_raw "$_line" "state")
                _added=$(json_extract_field_raw "$_line" "added_time")
                _adate=$(printf '%s' "$_added" | cut -c1-10)
                printf '%s\t%s\t%s\t%s\n' "$_tid" "$_url" "$_state" "${_adate:--}"
            done
        } > "$_list_tmp"
        print_tsv_head "$_list_tmp" 30
        rm -f "$_list_tmp"
        ;;

    quota)
        webmaster_get "/recrawl/quota" > "$TMPFILE"
        _body=$(cat "$TMPFILE")
        _daily=$(json_extract_number "$_body" "daily_quota")
        _remainder=$(json_extract_number "$_body" "quota_remainder")
        echo "=== Recrawl Quota ==="
        echo "Daily quota: ${_daily:-?}"
        echo "Remaining:   ${_remainder:-?}"
        ;;

    *)
        echo "Error: unknown action '$ACTION'. Use: submit, status, list, quota" >&2
        exit 1
        ;;
esac
