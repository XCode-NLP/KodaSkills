#!/bin/bash
# wb-card-content.sh — Fetch WB product card content (description + characteristics)
#
# IMPORTANT: This script does NOT call MPSTATS API. It uses Wildberries' internal
# CDN (basket-N.wbbasket.ru) which is NOT a documented public API. It works without
# any token but may change or break without notice. Use it when MPSTATS analytics
# is not enough and you need the actual card text — description, options,
# composition, exact dimensions, vendor_code, etc.
#
# Why this exists in mpstats skill: MPSTATS API is analytics-only and does not
# return card content (description/characteristics). For product card design,
# copy work, or content audits this data is required, so the skill ships this
# CDN helper to keep all WB-card workflows in one place.
#
# Usage: ./wb-card-content.sh <sku> [field]
#   sku    — WB product ID (numeric), e.g. 290784358
#   field  — optional jq path to extract a single field, e.g. .description
#            or .options. Without it, full JSON is printed.
#
# Examples:
#   ./wb-card-content.sh 290784358
#   ./wb-card-content.sh 290784358 .description
#   ./wb-card-content.sh 290784358 .grouped_options

set -e

if [ -z "$1" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
  sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

SKU="$1"
FIELD="${2:-}"

if ! [[ "$SKU" =~ ^[0-9]+$ ]]; then
  echo "Error: SKU must be numeric, got: $SKU" >&2
  exit 1
fi

# Path layout on basket CDN:
#   vol  = SKU / 100000  (integer division)
#   part = SKU / 1000    (integer division)
# basket-N number is determined by vol range and grows as WB scales.
# Mapping below is current as of 2026-05; update if a new basket appears.
vol=$((SKU / 100000))
part=$((SKU / 1000))

if   [ "$vol" -le 143  ]; then basket="01"
elif [ "$vol" -le 287  ]; then basket="02"
elif [ "$vol" -le 431  ]; then basket="03"
elif [ "$vol" -le 719  ]; then basket="04"
elif [ "$vol" -le 1007 ]; then basket="05"
elif [ "$vol" -le 1061 ]; then basket="06"
elif [ "$vol" -le 1115 ]; then basket="07"
elif [ "$vol" -le 1169 ]; then basket="08"
elif [ "$vol" -le 1313 ]; then basket="09"
elif [ "$vol" -le 1601 ]; then basket="10"
elif [ "$vol" -le 1655 ]; then basket="11"
elif [ "$vol" -le 1919 ]; then basket="12"
elif [ "$vol" -le 2045 ]; then basket="13"
elif [ "$vol" -le 2189 ]; then basket="14"
elif [ "$vol" -le 2405 ]; then basket="15"
elif [ "$vol" -le 2621 ]; then basket="16"
elif [ "$vol" -le 2837 ]; then basket="17"
elif [ "$vol" -le 3053 ]; then basket="18"
elif [ "$vol" -le 3269 ]; then basket="19"
elif [ "$vol" -le 3485 ]; then basket="20"
elif [ "$vol" -le 3701 ]; then basket="21"
elif [ "$vol" -le 3917 ]; then basket="22"
elif [ "$vol" -le 4133 ]; then basket="23"
elif [ "$vol" -le 4349 ]; then basket="24"
elif [ "$vol" -le 4565 ]; then basket="25"
elif [ "$vol" -le 4781 ]; then basket="26"
else basket="27"
fi

URL="https://basket-${basket}.wbbasket.ru/vol${vol}/part${part}/${SKU}/info/ru/card.json"

# Primary attempt with computed basket
RESPONSE=$(curl -sfL -A "Mozilla/5.0" "$URL" 2>/dev/null || true)

# Fallback: probe baskets 01..27 if mapping is stale (range tables drift over time)
if [ -z "$RESPONSE" ]; then
  for b in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27; do
    [ "$b" = "$basket" ] && continue
    TRY_URL="https://basket-${b}.wbbasket.ru/vol${vol}/part${part}/${SKU}/info/ru/card.json"
    RESPONSE=$(curl -sfL -A "Mozilla/5.0" "$TRY_URL" 2>/dev/null || true)
    if [ -n "$RESPONSE" ]; then
      URL="$TRY_URL"
      break
    fi
  done
fi

if [ -z "$RESPONSE" ]; then
  echo "Error: could not fetch card.json for SKU $SKU from any basket CDN." >&2
  echo "Tried: $URL" >&2
  echo "WB CDN may have changed. Inspect MPSTATS photo URL for current basket number:" >&2
  echo "  ./wb-sku.sh $SKU full | jq '.photo.list[0].f'" >&2
  exit 2
fi

if [ -n "$FIELD" ]; then
  echo "$RESPONSE" | jq -r "$FIELD"
else
  echo "$RESPONSE"
fi
