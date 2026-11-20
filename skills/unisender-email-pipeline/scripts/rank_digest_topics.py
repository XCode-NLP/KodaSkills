#!/usr/bin/env python3
"""Validate and rank business-profile digest topic candidates."""

from __future__ import annotations

import argparse
import json
import posixpath
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,79}$")
SCORE_FIELDS = ("demand", "momentum", "product_fit", "audience_value", "actionability", "novelty")
WEIGHTS = {
    "demand": 20,
    "momentum": 20,
    "product_fit": 20,
    "audience_value": 15,
    "actionability": 15,
    "novelty": 10,
}
WORDSTAT_STATUSES = {"complete", "partial", "missing"}
GENERAL_PATHS = {"/", "/news", "/blog", "/articles", "/category", "/tag", "/search"}


def load_payload(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    return payload


def validate_material_url(url: Any, prefix: str) -> str:
    if not isinstance(url, str) or not url:
        raise ValueError(f"{prefix} must be a non-empty URL")
    parts = urlsplit(url)
    host = parts.netloc.lower().removeprefix("www.")
    if parts.scheme != "https" or not host or parts.username or parts.password:
        raise ValueError(f"{prefix} must be an absolute HTTPS material URL without credentials")
    normalized_path = posixpath.normpath(parts.path).rstrip("/") or "/"
    if normalized_path in GENERAL_PATHS or re.search(r"/(category|tag|search)(/|$)", parts.path):
        raise ValueError(f"{prefix} must point to a concrete material, not a general section")
    return url


def validate_score(value: Any, prefix: str, allow_null: bool = False) -> float | None:
    if value is None and allow_null:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 5:
        raise ValueError(f"{prefix} must be a number from 0 to 5" + (" or null" if allow_null else ""))
    return float(value)


def rank(payload: dict[str, Any]) -> dict[str, Any]:
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not 5 <= len(candidates) <= 10:
        raise ValueError("candidates must contain 5–10 topic candidates")

    seen_ids: set[str] = set()
    unique_wordstat_phrases: set[str] = set()
    ranked: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        prefix = f"candidates[{index}]"
        if not isinstance(candidate, dict):
            raise ValueError(f"{prefix} must be an object")
        topic_id = candidate.get("id")
        if not isinstance(topic_id, str) or not ID_RE.fullmatch(topic_id):
            raise ValueError(f"{prefix}.id is invalid")
        if topic_id in seen_ids:
            raise ValueError(f"duplicate candidate id: {topic_id}")
        seen_ids.add(topic_id)
        title = candidate.get("title")
        axis = candidate.get("editorial_axis")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"{prefix}.title is required")
        if not isinstance(axis, str) or not axis.strip():
            raise ValueError(f"{prefix}.editorial_axis is required")

        material_urls = candidate.get("material_urls")
        if not isinstance(material_urls, list) or len(material_urls) > 5:
            raise ValueError(f"{prefix}.material_urls must contain 0–5 URLs")
        checked_urls = [validate_material_url(url, f"{prefix}.material_urls[{i}]") for i, url in enumerate(material_urls)]
        if len(checked_urls) != len(set(checked_urls)):
            raise ValueError(f"{prefix}.material_urls must be unique")

        status = candidate.get("wordstat_status")
        if status not in WORDSTAT_STATUSES:
            raise ValueError(f"{prefix}.wordstat_status must be complete, partial, or missing")
        scores = candidate.get("scores")
        if not isinstance(scores, dict):
            raise ValueError(f"{prefix}.scores must be an object")
        checked_scores: dict[str, float | None] = {}
        for field in SCORE_FIELDS:
            checked_scores[field] = validate_score(
                scores.get(field),
                f"{prefix}.scores.{field}",
                allow_null=field == "demand" and status != "complete",
            )
        if status == "missing" and checked_scores["demand"] is not None:
            raise ValueError(f"{prefix}.scores.demand must be null when Wordstat is missing")

        queries = candidate.get("wordstat_queries", [])
        if not isinstance(queries, list) or len(queries) > 3:
            raise ValueError(f"{prefix}.wordstat_queries must contain 0–3 queries")
        if status == "complete" and not queries:
            raise ValueError(f"{prefix}.wordstat_queries cannot be empty when Wordstat is complete")
        for query_index, query in enumerate(queries):
            query_prefix = f"{prefix}.wordstat_queries[{query_index}]"
            if not isinstance(query, dict) or not isinstance(query.get("phrase"), str) or not query["phrase"].strip():
                raise ValueError(f"{query_prefix}.phrase is required")
            unique_wordstat_phrases.add(query["phrase"].strip().casefold())
            frequency = query.get("frequency")
            if frequency is not None and (
                not isinstance(frequency, int) or isinstance(frequency, bool) or frequency < 0
            ):
                raise ValueError(f"{query_prefix}.frequency must be a non-negative integer or null")

        emerging_reason = candidate.get("emerging_reason")
        demand_value = checked_scores["demand"]
        if demand_value is not None and demand_value < 2:
            if checked_scores["momentum"] < 4 or checked_scores["product_fit"] < 4:
                emerging_reason = None
            elif not isinstance(emerging_reason, str) or not emerging_reason.strip():
                raise ValueError(
                    f"{prefix}.emerging_reason is required for a low-demand emerging topic with strong momentum and product fit"
                )

        effective_scores = {
            field: (2.5 if checked_scores[field] is None else checked_scores[field])
            for field in SCORE_FIELDS
        }
        score = sum(effective_scores[field] / 5 * WEIGHTS[field] for field in SCORE_FIELDS)
        penalty = 0 if status == "complete" else 5 if status == "partial" else 10
        final_score = max(0, score - penalty)
        eligible = len(checked_urls) >= 3
        warnings: list[str] = []
        if status != "complete":
            warnings.append(f"Wordstat evidence is {status}; applied {penalty}-point penalty")
        if not eligible:
            warnings.append("Fewer than three concrete materials")
        if demand_value is not None and demand_value < 2 and emerging_reason:
            warnings.append("Low demand accepted only as an emerging-topic exception")

        ranked.append(
            {
                **candidate,
                "scores": checked_scores,
                "topic_score": round(final_score, 2),
                "eligible": eligible,
                "warnings": warnings,
            }
        )

    if len(unique_wordstat_phrases) > 15:
        raise ValueError("no more than 15 unique Wordstat seed phrases are allowed per digest")

    ranked.sort(key=lambda item: (-item["topic_score"], item["id"]))
    selected = next((item["id"] for item in ranked if item["eligible"]), None)
    return {
        "status": "complete" if selected and all(item["wordstat_status"] == "complete" for item in ranked) else "partial",
        "candidate_count": len(ranked),
        "selected_candidate_id": selected,
        "ranked_candidates": ranked,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON object with candidates[]")
    parser.add_argument("--output", type=Path, help="Optional output JSON path")
    args = parser.parse_args()
    result = rank(load_payload(args.input))
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if result["selected_candidate_id"] is None:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
