#!/bin/sh
# Add a site to Yandex Webmaster
# Usage: add_site.sh --url <site_url>

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config

URL=""

while [ $# -gt 0 ]; do
    case "$1" in
        --url) URL="$2"; shift 2 ;;
        *)     shift ;;
    esac
done

if [ -z "$URL" ]; then
    echo "Error: --url <site_url> is required." >&2
    echo "Example: bash scripts/add_site.sh --url https://example.com" >&2
    exit 1
fi

ensure_user_id

TMPFILE="${WM_TMPDIR}/wm_add_site_$$.json"
trap 'rm -f "$TMPFILE"' EXIT

_escaped_url=$(json_escape "$URL")
webmaster_user_post "/hosts" "{\"host_url\":\"$_escaped_url\"}" > "$TMPFILE"

_host_id=$(json_extract_field_raw "$(cat "$TMPFILE")" "host_id")

echo "Site added successfully."
echo "Host ID: $_host_id"
echo ""
echo "Next step: verify ownership with:"
echo "  bash scripts/verify.sh --host-id \"$_host_id\" --action get --method DNS"

# Invalidate hosts cache
rm -f "$CACHE_DIR/hosts.tsv" "$CACHE_DIR/hosts.json"
echo "(hosts cache invalidated)"
