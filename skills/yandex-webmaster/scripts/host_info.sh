#!/bin/sh
# Get site details and owners
# Usage: host_info.sh --host <domain> | --host-id <id>

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config

parse_host_params "$@"
ensure_user_id
resolve_host
require_host

TMPFILE="${WM_TMPDIR}/wm_host_info_$$.json"
trap 'rm -f "$TMPFILE" "${TMPFILE}_owners"' EXIT

# Get host info
webmaster_get "" > "$TMPFILE"

echo "=== Site Info ==="
_hi_url=$(json_extract_field_raw "$(cat "$TMPFILE")" "ascii_host_url")
_hi_ver=$(json_extract_bool "$(cat "$TMPFILE")" "verified")
_hi_status=$(json_extract_field_raw "$(cat "$TMPFILE")" "host_data_status")
_hi_display=$(json_extract_field_raw "$(cat "$TMPFILE")" "host_display_name")
_hi_mirror=$(json_extract_field_raw "$(cat "$TMPFILE")" "ascii_host_url")

echo "Host ID:      $HOST_ID"
echo "URL:          $_hi_url"
echo "Display name: ${_hi_display:--}"
echo "Verified:     $_hi_ver"
echo "Data status:  ${_hi_status:--}"

# Get owners
echo ""
echo "=== Owners ==="
webmaster_get "/owners" > "${TMPFILE}_owners"

echo "login	verification_type	verification_date"
tr -d '\n\r' < "${TMPFILE}_owners" | sed 's/},{/}\n{/g' | while IFS= read -r _line || [ -n "$_line" ]; do
    _login=$(json_extract_field_raw "$_line" "user_login")
    _vtype=$(json_extract_field_raw "$_line" "verification_type")
    _vdate=$(json_extract_field_raw "$_line" "verification_date")
    [ -z "$_login" ] && continue
    printf '%s\t%s\t%s\n' "$_login" "$_vtype" "${_vdate:--}"
done
