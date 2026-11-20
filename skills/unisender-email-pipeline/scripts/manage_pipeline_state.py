#!/usr/bin/env python3
"""Validate, plan, and merge persistent email-pipeline state."""

from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime
from pathlib import Path
from typing import Any


LIST_KEYS = {
    "baseline_snapshots": "snapshot_id",
    "campaign_observations": ("campaign_id", "observation_window", "as_of"),
    "link_snapshots": "snapshot_id",
    "web_analytics_snapshots": "snapshot_id",
    "crm_snapshots": "snapshot_id",
    "wordstat_observations": ("phrase", "region", "observed_at"),
    "content_registry": "canonical_url",
    "recommendations": "recommendation_id",
    "experiments": "experiment_id",
    "draft_registry": "draft_key",
    "run_history": "run_id",
}

REQUIRED_TOP = {
    "schema_version",
    "project_key",
    "state_revision",
    "updated_at",
    "coverage",
    *LIST_KEYS,
}


def load(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("state must be a JSON object")
    return value


def dump(value: dict[str, Any], path: str | None) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if path:
        Path(path).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def parse_datetime(value: str, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO-8601 string")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} is not valid ISO-8601: {value}") from exc


def item_key(item: dict[str, Any], spec: str | tuple[str, ...]) -> tuple[Any, ...]:
    fields = (spec,) if isinstance(spec, str) else spec
    values = tuple(item.get(field) for field in fields)
    if any(value in (None, "") for value in values):
        raise ValueError(f"missing stable key {fields}: {item}")
    return values


def validate(state: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    missing = sorted(REQUIRED_TOP - set(state))
    if missing:
        errors.append("missing top-level fields: " + ", ".join(missing))
    if state.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    if not isinstance(state.get("state_revision"), int) or state.get("state_revision", -1) < 0:
        errors.append("state_revision must be a non-negative integer")
    try:
        parse_datetime(state.get("updated_at"), "updated_at")
    except ValueError as exc:
        errors.append(str(exc))
    if not isinstance(state.get("coverage"), dict):
        errors.append("coverage must be an object")
    for name, spec in LIST_KEYS.items():
        items = state.get(name)
        if not isinstance(items, list):
            errors.append(f"{name} must be an array")
            continue
        seen: set[tuple[Any, ...]] = set()
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"{name}[{index}] must be an object")
                continue
            try:
                key = item_key(item, spec)
            except ValueError as exc:
                errors.append(f"{name}[{index}]: {exc}")
                continue
            if key in seen:
                errors.append(f"{name} contains duplicate key {key}")
            seen.add(key)
    return {"status": "passed" if not errors else "blocked", "errors": errors}


def enrich(old: Any, new: Any) -> Any:
    if new is None:
        return copy.deepcopy(old)
    if isinstance(old, dict) and isinstance(new, dict):
        result = copy.deepcopy(old)
        for key, value in new.items():
            result[key] = enrich(result.get(key), value)
        return result
    if isinstance(old, list) and isinstance(new, list) and all(not isinstance(x, (dict, list)) for x in old + new):
        return copy.deepcopy(list(dict.fromkeys(old + new)))
    return copy.deepcopy(new)


def merge_lists(base: list[dict[str, Any]], delta: list[dict[str, Any]], spec: str | tuple[str, ...]) -> list[dict[str, Any]]:
    result = {item_key(item, spec): copy.deepcopy(item) for item in base}
    for item in delta:
        key = item_key(item, spec)
        if spec == "draft_key" and key in result:
            old_message_id = result[key].get("message_id")
            new_message_id = item.get("message_id")
            if old_message_id and (not new_message_id or (isinstance(new_message_id, str) and new_message_id.strip().lower() in {"", "unknown", "missing"})):
                item = {**item, "message_id": None}
                new_message_id = None
            if old_message_id and new_message_id and old_message_id != new_message_id:
                raise ValueError(f"draft {key[0]} has conflicting message_id values")
            if result[key].get("status") in {"created", "existing_unchanged"} and item.get("status") in {"unknown", "missing"}:
                item = {**item, "status": None}
        result[key] = enrich(result.get(key, {}), item)
    return [result[key] for key in sorted(result, key=lambda value: tuple(str(x) for x in value))]


def merge(base: dict[str, Any], delta: dict[str, Any]) -> dict[str, Any]:
    base_check = validate(base)
    if base_check["status"] != "passed":
        raise ValueError("base state is invalid: " + "; ".join(base_check["errors"]))
    result = copy.deepcopy(base)
    for field, value in delta.items():
        if field in LIST_KEYS:
            if not isinstance(value, list):
                raise ValueError(f"delta.{field} must be an array")
            result[field] = merge_lists(result[field], value, LIST_KEYS[field])
        elif field not in {"schema_version", "project_key", "state_revision"}:
            result[field] = enrich(result.get(field), value)
    if delta.get("project_key") not in (None, base["project_key"]):
        raise ValueError("delta project_key does not match base state")
    result["schema_version"] = 1
    result["project_key"] = base["project_key"]
    result["state_revision"] = base["state_revision"] + 1
    if "updated_at" not in delta:
        raise ValueError("delta.updated_at is required")
    parse_datetime(delta["updated_at"], "delta.updated_at")
    result["updated_at"] = delta["updated_at"]
    check = validate(result)
    if check["status"] != "passed":
        raise ValueError("merged state is invalid: " + "; ".join(check["errors"]))
    return result


def plan(state: dict[str, Any], as_of: str) -> dict[str, Any]:
    check = validate(state)
    if check["status"] != "passed":
        raise ValueError("state is invalid: " + "; ".join(check["errors"]))
    now = parse_datetime(as_of, "as_of")
    gaps: list[dict[str, Any]] = []
    mature: list[dict[str, Any]] = []
    wordstat_refresh: list[dict[str, Any]] = []
    for snapshot in state["baseline_snapshots"]:
        for source, status in snapshot.get("source_status", {}).items():
            if status in {"missing", "partial"}:
                gaps.append({"snapshot_id": snapshot["snapshot_id"], "source": source, "status": status})
    for item in state["campaign_observations"]:
        for source, status in item.get("source_status", {}).items():
            if status in {"missing", "partial"}:
                gaps.append({"campaign_id": item["campaign_id"], "source": source, "status": status})
        if item.get("observation_window") in {"D+1", "D+3"} and item.get("sent_at"):
            sent = parse_datetime(item["sent_at"], "sent_at")
            age_days = (now - sent.astimezone(now.tzinfo)).total_seconds() / 86400
            if age_days >= 7:
                mature.append({"campaign_id": item["campaign_id"], "age_days": round(age_days, 2), "target_window": "D+7"})
    for item in state["wordstat_observations"]:
        observed = parse_datetime(item["observed_at"], "observed_at")
        age_days = (now - observed.astimezone(now.tzinfo)).total_seconds() / 86400
        if age_days >= 28:
            wordstat_refresh.append({"phrase": item["phrase"], "region": item["region"], "age_days": round(age_days, 2)})
    open_experiments = [x for x in state["experiments"] if x.get("status") in {"planned", "running", "awaiting_result"}]
    return {
        "status": "complete",
        "as_of": as_of,
        "state_revision": state["state_revision"],
        "fetch_campaigns_after": state.get("coverage", {}).get("baseline_through_sent_at"),
        "mature_campaigns": mature,
        "source_gaps": gaps,
        "wordstat_refresh": wordstat_refresh,
        "previous_experiment": open_experiments[-1] if open_experiments else None,
        "known_draft_keys": [x["draft_key"] for x in state["draft_registry"]],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("state")
    plan_parser = sub.add_parser("plan")
    plan_parser.add_argument("state")
    plan_parser.add_argument("--as-of", required=True)
    plan_parser.add_argument("--output")
    merge_parser = sub.add_parser("merge")
    merge_parser.add_argument("state")
    merge_parser.add_argument("delta")
    merge_parser.add_argument("--output", required=True)
    args = parser.parse_args()

    try:
        if args.command == "validate":
            result = validate(load(args.state))
            dump(result, None)
            raise SystemExit(0 if result["status"] == "passed" else 1)
        if args.command == "plan":
            dump(plan(load(args.state), args.as_of), args.output)
            return
        dump(merge(load(args.state), load(args.delta)), args.output)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
