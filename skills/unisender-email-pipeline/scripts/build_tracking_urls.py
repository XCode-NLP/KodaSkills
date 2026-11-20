#!/usr/bin/env python3
"""Build deterministic, privacy-safe UniSender tracking URLs for email placements."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


CAMPAIGN_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,119}$")
PLACEMENT_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,79}$")
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
PII_KEYS = {
    "email",
    "e-mail",
    "mail",
    "phone",
    "telephone",
    "tel",
    "name",
    "first_name",
    "last_name",
    "fio",
}
MANAGED_UTM = {"utm_source", "utm_medium", "utm_campaign", "utm_content"}


def load_payload(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict) or not isinstance(payload.get("placements"), list):
        raise ValueError("input must be an object with a placements array")
    return payload


def validate_url(url: str, placement_id: str) -> tuple[Any, list[tuple[str, str]]]:
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.netloc:
        raise ValueError(f"{placement_id}: URL must be absolute HTTPS")
    query = parse_qsl(parts.query, keep_blank_values=True)
    # Check alternate query separators without changing the original URL semantics.
    privacy_query = parse_qsl(parts.query.replace(";", "&"), keep_blank_values=True)
    for key, value in privacy_query:
        if EMAIL_RE.search(key):
            raise ValueError(f"{placement_id}: email-like query key is prohibited")
        if key.lower() in PII_KEYS:
            raise ValueError(f"{placement_id}: prohibited PII query key: {key}")
        if EMAIL_RE.search(value):
            raise ValueError(f"{placement_id}: email-like query value is prohibited")
    return parts, query


def build(payload: dict[str, Any], campaign: str) -> dict[str, Any]:
    if not CAMPAIGN_RE.fullmatch(campaign):
        raise ValueError("campaign must contain lowercase letters, digits, hyphens or underscores")

    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for index, item in enumerate(payload["placements"]):
        if not isinstance(item, dict):
            raise ValueError(f"placements[{index}] must be an object")
        placement_id = item.get("id")
        url = item.get("url")
        track = item.get("track", True)
        if not isinstance(placement_id, str) or not PLACEMENT_RE.fullmatch(placement_id):
            raise ValueError(f"placements[{index}].id is invalid")
        if placement_id in seen:
            raise ValueError(f"duplicate placement id: {placement_id}")
        seen.add(placement_id)
        if not isinstance(url, str) or not url:
            raise ValueError(f"{placement_id}: url is required")
        if not isinstance(track, bool):
            raise ValueError(f"{placement_id}: track must be boolean")

        parts, query = validate_url(url, placement_id)
        if not track:
            output.append({"id": placement_id, "original_url": url, "url": url, "tracked": False})
            continue

        preserved = [(key, value) for key, value in query if key.lower() not in MANAGED_UTM]
        tracked_query = preserved + [
            ("utm_source", "unisender"),
            ("utm_medium", "email"),
            ("utm_campaign", campaign),
            ("utm_content", placement_id),
        ]
        tracked_url = urlunsplit(
            (parts.scheme, parts.netloc, parts.path, urlencode(tracked_query, doseq=True), parts.fragment)
        )
        output.append(
            {"id": placement_id, "original_url": url, "url": tracked_url, "tracked": True}
        )

    return {"utm_campaign": campaign, "placement_count": len(output), "placements": output}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON object with placements[]")
    parser.add_argument("--campaign", required=True, help="Stable lowercase utm_campaign slug")
    parser.add_argument("--output", type=Path, help="Optional output JSON path")
    args = parser.parse_args()

    result = build(load_payload(args.input), args.campaign)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    try:
        main()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
