#!/bin/sh
# Sitemap management
# Usage: sitemaps.sh --host <domain> --action list|user-list|info|add|recrawl-limit|recrawl
#        [--sitemap-id ID] [--url URL] [--limit N]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config

SITEMAP_ID=""
SITEMAP_URL=""

_args=""
while [ $# -gt 0 ]; do
    case "$1" in
        --sitemap-id) SITEMAP_ID="$2"; shift 2 ;;
        --url)        SITEMAP_URL="$2"; shift 2 ;;
        *)            _args="$_args $1"; shift ;;
    esac
done
# shellcheck disable=SC2086
parse_host_params $_args
ensure_user_id
resolve_host
require_host

ACTION="${ACTION:-list}"
TMPFILE="${WM_TMPDIR}/wm_sitemaps_$$.json"
trap 'rm -f "$TMPFILE"' EXIT

case "$ACTION" in
    list)
        _curl_args=""
        if [ -n "$LIMIT" ]; then
            _curl_args="--data-urlencode limit=$LIMIT"
        fi
        # shellcheck disable=SC2086
        webmaster_get "/sitemaps" $_curl_args > "$TMPFILE"

        echo "sitemap_id	url	urls_count	errors	type	sources"
        tr -d '\n\r' < "$TMPFILE" | sed 's/},{/}\n{/g' | while IFS= read -r _line || [ -n "$_line" ]; do
            _sid=$(json_extract_field_raw "$_line" "sitemap_id")
            [ -z "$_sid" ] && continue
            _surl=$(json_extract_field_raw "$_line" "sitemap_url")
            _ucnt=$(json_extract_number "$_line" "urls_count")
            _ecnt=$(json_extract_number "$_line" "errors_count")
            _stype=$(json_extract_field_raw "$_line" "sitemap_type")
            _src=$(json_extract_array_strings "$_line" "sources" | tr '\n' ',' | sed 's/,$//')
            printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$_sid" "$_surl" "${_ucnt:-0}" "${_ecnt:-0}" "${_stype:--}" "${_src:--}"
        done
        ;;

    user-list)
        _curl_args=""
        if [ -n "$LIMIT" ]; then
            _curl_args="--data-urlencode limit=$LIMIT"
        fi
        if [ -n "$OFFSET" ]; then
            _curl_args="$_curl_args --data-urlencode offset=$OFFSET"
        fi
        # shellcheck disable=SC2086
        webmaster_get "/user-added-sitemaps" $_curl_args > "$TMPFILE"

        echo "sitemap_id	url	added_date"
        tr -d '\n\r' < "$TMPFILE" | sed 's/},{/}\n{/g' | while IFS= read -r _line || [ -n "$_line" ]; do
            _sid=$(json_extract_field_raw "$_line" "sitemap_id")
            [ -z "$_sid" ] && continue
            _surl=$(json_extract_field_raw "$_line" "sitemap_url")
            _added=$(json_extract_field_raw "$_line" "added_date")
            printf '%s\t%s\t%s\n' "$_sid" "$_surl" "${_added:--}"
        done
        ;;

    info)
        if [ -z "$SITEMAP_ID" ]; then
            echo "Error: --sitemap-id is required for --action info" >&2
            exit 1
        fi
        webmaster_get "/sitemaps/${SITEMAP_ID}" > "$TMPFILE"
        _body=$(cat "$TMPFILE")
        echo "=== Sitemap Info ==="
        echo "ID:         $(json_extract_field_raw "$_body" "sitemap_id")"
        echo "URL:        $(json_extract_field_raw "$_body" "sitemap_url")"
        echo "URLs count: $(json_extract_number "$_body" "urls_count")"
        echo "Errors:     $(json_extract_number "$_body" "errors_count")"
        echo "Children:   $(json_extract_number "$_body" "children_count")"
        echo "Type:       $(json_extract_field_raw "$_body" "sitemap_type")"
        echo "Last access:$(json_extract_field_raw "$_body" "last_access_date")"
        ;;

    add)
        if [ -z "$SITEMAP_URL" ]; then
            echo "Error: --url is required for --action add" >&2
            exit 1
        fi
        webmaster_post "/user-added-sitemaps" "{\"url\":\"$SITEMAP_URL\"}" > "$TMPFILE"
        _sid=$(json_extract_field_raw "$(cat "$TMPFILE")" "sitemap_id")
        echo "Sitemap added."
        echo "Sitemap ID: $_sid"
        ;;

    recrawl-limit)
        # Uses v4.1 API
        webmaster_raw_get "/v4.1/user/${USER_ID}/hosts/${HOST_ID}/sitemaps/recrawl" > "$TMPFILE"
        _body=$(cat "$TMPFILE")
        _monthly=$(json_extract_number "$_body" "monthly_limit_requests")
        _used=$(json_extract_number "$_body" "requests_count")
        _nearest=$(json_extract_field_raw "$_body" "nearest_allowed_day")
        echo "=== Sitemap Priority Recrawl Limits ==="
        echo "Monthly limit: ${_monthly:-?}"
        echo "Used:          ${_used:-0}"
        echo "Next allowed:  ${_nearest:--}"
        ;;

    recrawl)
        if [ -z "$SITEMAP_ID" ]; then
            echo "Error: --sitemap-id is required for --action recrawl" >&2
            exit 1
        fi
        # Uses v4.1 API
        webmaster_raw_post "/v4.1/user/${USER_ID}/hosts/${HOST_ID}/sitemaps/${SITEMAP_ID}/recrawl" "{}" > "$TMPFILE"
        _body=$(cat "$TMPFILE")
        _pending=$(json_extract_bool "$_body" "pending")
        _allowed=$(json_extract_bool "$_body" "allowed")
        echo "Sitemap recrawl requested."
        echo "Pending: ${_pending:-?}"
        echo "Allowed: ${_allowed:-?}"
        ;;

    *)
        echo "Error: unknown action '$ACTION'. Use: list, user-list, info, add, recrawl-limit, recrawl" >&2
        exit 1
        ;;
esac
