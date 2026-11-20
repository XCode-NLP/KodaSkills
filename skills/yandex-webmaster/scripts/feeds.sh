#!/bin/sh
# YML Feeds management — list, add, batch-add, change regions, check status
# Usage: feeds.sh --host <domain> --action list|add|batch-add|change|add-status
#        [--url URL] [--type REALTY|VACANCY|GOODS|DOCTORS|CARS|SERVICES|EDUCATION|ACTIVITY]
#        [--region-ids "225,213"] [--request-id ID]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config

FEED_URL=""
FEED_TYPE=""
REGION_IDS=""
REQUEST_ID=""

_args=""
while [ $# -gt 0 ]; do
    case "$1" in
        --url)        FEED_URL="$2"; shift 2 ;;
        --type)       FEED_TYPE="$2"; shift 2 ;;
        --region-ids) REGION_IDS="$2"; shift 2 ;;
        --request-id) REQUEST_ID="$2"; shift 2 ;;
        *)            _args="$_args $1"; shift ;;
    esac
done
# shellcheck disable=SC2086
parse_host_params $_args
ensure_user_id
resolve_host
require_host

ACTION="${ACTION:-list}"
TMPFILE="${WM_TMPDIR}/wm_feeds_$$.json"
trap 'rm -f "$TMPFILE"' EXIT

case "$ACTION" in
    list)
        webmaster_get "/feeds/list" > "$TMPFILE"

        _list_tmp="${WM_TMPDIR}/wm_feeds_list_$$.tsv"
        {
            echo "url	type	regions"
            tr -d '\n\r' < "$TMPFILE" | sed 's/},{/}\n{/g' | while IFS= read -r _line || [ -n "$_line" ]; do
                _furl=$(json_extract_field_raw "$_line" "url")
                [ -z "$_furl" ] && continue
                _ftype=$(json_extract_field_raw "$_line" "type")
                _fregs=$(printf '%s' "$_line" | grep -o '"regionIds"[[:space:]]*:\[[^]]*\]' | head -1 | grep -o '[0-9]*' | tr '\n' ',' | sed 's/,$//')
                printf '%s\t%s\t%s\n' "$_furl" "${_ftype:--}" "${_fregs:--}"
            done
        } > "$_list_tmp"
        print_tsv_head "$_list_tmp" 30
        rm -f "$_list_tmp"
        ;;

    add)
        if [ -z "$FEED_URL" ] || [ -z "$FEED_TYPE" ]; then
            echo "Error: --url and --type are required for --action add" >&2
            exit 1
        fi

        _escaped_furl=$(json_escape "$FEED_URL")
        _json="{\"url\":\"$_escaped_furl\",\"type\":\"$FEED_TYPE\""
        if [ -n "$REGION_IDS" ]; then
            _json="$_json,\"regionIds\":[$REGION_IDS]"
        fi
        _json="$_json}"

        webmaster_post "/feeds/add/start" "$_json" > "$TMPFILE"
        _rid=$(json_extract_field_raw "$(cat "$TMPFILE")" "requestId")
        echo "Feed upload started."
        echo "Request ID: $_rid"
        echo "Check status: bash scripts/feeds.sh --host ... --action add-status --request-id $_rid"
        ;;

    batch-add)
        # Reads feed definitions from stdin (JSON array)
        # Example: echo '[{"url":"https://a.com/f.yml","type":"GOODS"},{"url":"https://b.com/f.yml","type":"REALTY","regionIds":[213]}]' | bash scripts/feeds.sh --host ... --action batch-add
        if [ -t 0 ]; then
            echo "Error: batch-add reads JSON array from stdin." >&2
            echo "Example: echo '[{\"url\":\"...\",\"type\":\"GOODS\"}]' | bash scripts/feeds.sh --host ... --action batch-add" >&2
            exit 1
        fi

        _batch_body=$(cat)
        webmaster_post "/feeds/batch/add" "$_batch_body" > "$TMPFILE"

        echo "url	status"
        tr -d '\n\r' < "$TMPFILE" | sed 's/},{/}\n{/g' | while IFS= read -r _line || [ -n "$_line" ]; do
            _burl=$(json_extract_field_raw "$_line" "url")
            [ -z "$_burl" ] && continue
            _bstatus=$(json_extract_field_raw "$_line" "status")
            printf '%s\t%s\n' "$_burl" "$_bstatus"
        done
        ;;

    change)
        if [ -z "$FEED_URL" ] || [ -z "$REGION_IDS" ]; then
            echo "Error: --url and --region-ids are required for --action change" >&2
            exit 1
        fi

        _escaped_furl=$(json_escape "$FEED_URL")
        webmaster_post "/feeds/change" "{\"url\":\"$_escaped_furl\",\"newRegionIds\":[$REGION_IDS]}" > "$TMPFILE"
        echo "Feed regions updated."
        ;;

    add-status)
        if [ -z "$REQUEST_ID" ]; then
            echo "Error: --request-id is required for --action add-status" >&2
            exit 1
        fi

        webmaster_get "/feeds/add/info" --data-urlencode "requestId=$REQUEST_ID" > "$TMPFILE"
        _status=$(json_extract_field_raw "$(cat "$TMPFILE")" "processStatus")
        echo "Upload status: $_status"
        ;;

    *)
        echo "Error: unknown action '$ACTION'. Use: list, add, change, add-status" >&2
        exit 1
        ;;
esac
