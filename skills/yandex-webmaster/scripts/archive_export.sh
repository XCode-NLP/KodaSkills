#!/bin/sh
# Export all indexed pages archive
# Usage: archive_export.sh --host <domain> --action start|status [--task-id ID]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config

TASK_ID=""

_args=""
while [ $# -gt 0 ]; do
    case "$1" in
        --task-id) TASK_ID="$2"; shift 2 ;;
        *)         _args="$_args $1"; shift ;;
    esac
done
# shellcheck disable=SC2086
parse_host_params $_args
ensure_user_id
resolve_host
require_host

ACTION="${ACTION:-start}"
TMPFILE="${WM_TMPDIR}/wm_archive_$$.json"
trap 'rm -f "$TMPFILE"' EXIT

case "$ACTION" in
    start)
        webmaster_raw_post "/v4/user/${USER_ID}/hosts/${HOST_ID}/indexing/archive/" "{}" > "$TMPFILE"
        _tid=$(json_extract_field_raw "$(cat "$TMPFILE")" "task_id")
        echo "Archive export started."
        echo "Task ID: $_tid"
        echo "Check status: bash scripts/archive_export.sh --host ... --action status --task-id $_tid"
        echo "(Generation takes 10 seconds to 3 minutes)"
        ;;

    status)
        if [ -z "$TASK_ID" ]; then
            echo "Error: --task-id is required for --action status" >&2
            exit 1
        fi
        webmaster_raw_get "/v4/user/${USER_ID}/hosts/${HOST_ID}/indexing/archive/${TASK_ID}" > "$TMPFILE"
        _body=$(cat "$TMPFILE")
        _state=$(json_extract_field_raw "$_body" "state")
        _url=$(json_extract_field_raw "$_body" "download_url")

        echo "=== Archive Export ==="
        echo "Task ID: $TASK_ID"
        echo "State:   $_state"
        if [ -n "$_url" ]; then
            echo "Download: $_url"
            echo "(URL valid for 24 hours)"
        fi
        ;;

    *)
        echo "Error: unknown action '$ACTION'. Use: start, status" >&2
        exit 1
        ;;
esac
