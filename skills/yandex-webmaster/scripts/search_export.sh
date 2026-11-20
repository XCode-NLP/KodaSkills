#!/bin/sh
# PRO SERP export — available dates, limits, init export, check status
# Usage: search_export.sh --host <domain> --action dates|limits|start|status
#        [--dates "2025-01-01,2025-01-02"] [--paths "/,/catalog/"]
#        [--region-ids "213"] [--task-id ID]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config

EXPORT_DATES=""
EXPORT_PATHS=""
REGION_IDS=""
TASK_ID=""

_args=""
while [ $# -gt 0 ]; do
    case "$1" in
        --dates)      EXPORT_DATES="$2"; shift 2 ;;
        --paths)      EXPORT_PATHS="$2"; shift 2 ;;
        --region-ids) REGION_IDS="$2"; shift 2 ;;
        --task-id)    TASK_ID="$2"; shift 2 ;;
        *)            _args="$_args $1"; shift ;;
    esac
done
# shellcheck disable=SC2086
parse_host_params $_args
ensure_user_id
resolve_host
require_host

ACTION="${ACTION:-dates}"
TMPFILE="${WM_TMPDIR}/wm_export_$$.json"
trap 'rm -f "$TMPFILE"' EXIT

_pro_base="/v4/user/${USER_ID}/hosts/${HOST_ID}/pro"

case "$ACTION" in
    dates)
        webmaster_raw_get "${_pro_base}/serp/dates" > "$TMPFILE"
        echo "=== Available Export Dates ==="
        json_extract_array_strings "$(cat "$TMPFILE")" "dates"
        ;;

    limits)
        webmaster_raw_get "${_pro_base}/limits" > "$TMPFILE"

        echo "owner	feature	limit	used	remaining	active	period"
        tr -d '\n\r' < "$TMPFILE" | sed 's/},{/}\n{/g' | while IFS= read -r _line || [ -n "$_line" ]; do
            _owner=$(json_extract_field_raw "$_line" "owner")
            [ -z "$_owner" ] && continue
            _feat=$(json_extract_field_raw "$_line" "feature")
            _lim=$(json_extract_number "$_line" "limit")
            _used=$(json_extract_number "$_line" "used")
            _rem=$(json_extract_number "$_line" "remaining")
            _active=$(json_extract_bool "$_line" "is_active")
            _pstart=$(json_extract_field_raw "$_line" "period_start")
            _pend=$(json_extract_field_raw "$_line" "period_end")
            printf '%s\t%s\t%s\t%s\t%s\t%s\t%s..%s\n' "$_owner" "$_feat" "${_lim:-0}" "${_used:-0}" "${_rem:-0}" "${_active:--}" "${_pstart:--}" "${_pend:--}"
        done
        ;;

    start)
        if [ -z "$EXPORT_DATES" ] || [ -z "$EXPORT_PATHS" ]; then
            echo "Error: --dates and --paths are required for --action start" >&2
            echo "Example: --dates '\"2025-01-01\",\"2025-01-02\"' --paths '\"/\",\"/catalog/\"'" >&2
            exit 1
        fi

        _json="{\"dates\":[$EXPORT_DATES],\"paths\":[$EXPORT_PATHS]"
        if [ -n "$REGION_IDS" ]; then
            _json="$_json,\"region_ids\":[$REGION_IDS]"
        fi
        _json="$_json,\"use_pro_tariff\":\"false\"}"

        webmaster_raw_post "${_pro_base}/serp/queries/download/" "$_json" > "$TMPFILE"
        _body=$(cat "$TMPFILE")
        _tid=$(json_extract_field_raw "$_body" "task_id")
        _free_used=$(json_extract_number "$_body" "free_quota_used")
        _free_rem=$(json_extract_number "$_body" "free_quota_remaining")

        echo "Export started."
        echo "Task ID:              $_tid"
        echo "Free quota used:      ${_free_used:-0}"
        echo "Free quota remaining: ${_free_rem:-?}"
        echo "Check status: bash scripts/search_export.sh --host ... --action status --task-id $_tid"
        ;;

    status)
        if [ -z "$TASK_ID" ]; then
            echo "Error: --task-id is required for --action status" >&2
            exit 1
        fi
        webmaster_raw_get "${_pro_base}/serp/queries/download/${TASK_ID}" > "$TMPFILE"
        _body=$(cat "$TMPFILE")
        _status=$(json_extract_field_raw "$_body" "download_status")
        _url=$(json_extract_field_raw "$_body" "url")

        echo "=== Export Status ==="
        echo "Task ID: $TASK_ID"
        echo "Status:  $_status"
        if [ -n "$_url" ]; then
            echo "Download: $_url"
            echo "(URL valid for 24 hours)"
        fi
        ;;

    *)
        echo "Error: unknown action '$ACTION'. Use: dates, limits, start, status" >&2
        exit 1
        ;;
esac
