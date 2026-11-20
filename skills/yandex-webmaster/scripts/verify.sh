#!/bin/sh
# Verify site ownership in Yandex Webmaster
# Usage: verify.sh --host <domain> --action get|start --method DNS|HTML_FILE|META_TAG

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config

METHOD=""

# Parse params (include --method before common parsing)
_args=""
while [ $# -gt 0 ]; do
    case "$1" in
        --method) METHOD="$2"; shift 2 ;;
        *)        _args="$_args $1"; shift ;;
    esac
done
# shellcheck disable=SC2086
parse_host_params $_args
ensure_user_id
resolve_host
require_host

ACTION="${ACTION:-get}"

TMPFILE="${WM_TMPDIR}/wm_verify_$$.json"
trap 'rm -f "$TMPFILE"' EXIT

case "$ACTION" in
    get)
        # Get verification info and code
        webmaster_get "/verification" > "$TMPFILE"
        _body=$(cat "$TMPFILE")

        _state=$(json_extract_field_raw "$_body" "verification_state")
        _uin=$(json_extract_field_raw "$_body" "verification_uin")
        _type=$(json_extract_field_raw "$_body" "verification_type")
        _time=$(json_extract_field_raw "$_body" "latest_verification_time")

        echo "=== Verification Status ==="
        echo "State:    $_state"
        echo "Type:     ${_type:--}"
        echo "Code:     ${_uin:--}"
        echo "Last try: ${_time:--}"

        if [ "$_state" != "VERIFIED" ] && [ -n "$_uin" ]; then
            echo ""
            echo "=== How to verify ==="
            echo "DNS:       Add TXT record: yandex-verification: $_uin"
            echo "HTML_FILE: Create file yandex_${_uin}.html in site root"
            echo "META_TAG:  Add <meta name=\"yandex-verification\" content=\"$_uin\" />"
            echo ""
            echo "Then run: bash scripts/verify.sh --host-id \"$HOST_ID\" --action start --method DNS"
        fi

        _verifiers=$(json_extract_array_strings "$_body" "applicable_verifiers")
        if [ -n "$_verifiers" ]; then
            echo ""
            echo "Available methods: $(echo "$_verifiers" | tr '\n' ', ' | sed 's/,$//')"
        fi
        ;;

    start)
        if [ -z "$METHOD" ]; then
            echo "Error: --method <DNS|HTML_FILE|META_TAG> is required for --action start." >&2
            exit 1
        fi

        webmaster_raw_post "/v4/user/${USER_ID}/hosts/${HOST_ID}/verification?verification_type=${METHOD}" "{}" > "$TMPFILE"
        _body=$(cat "$TMPFILE")

        _state=$(json_extract_field_raw "$_body" "verification_state")
        _type=$(json_extract_field_raw "$_body" "verification_type")

        echo "Verification initiated."
        echo "Method: $_type"
        echo "State:  $_state"

        if [ "$_state" = "VERIFIED" ]; then
            echo "Site is now VERIFIED."
            # Invalidate hosts cache
            rm -f "$CACHE_DIR/hosts.tsv" "$CACHE_DIR/hosts.json"
            echo "(hosts cache invalidated)"
        elif [ "$_state" = "VERIFICATION_FAILED" ]; then
            echo "Verification FAILED. Check that the verification record is in place."
        fi
        ;;

    *)
        echo "Error: unknown action '$ACTION'. Use: get, start" >&2
        exit 1
        ;;
esac
