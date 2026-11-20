#!/usr/bin/env python3
"""Validate normalized email campaign data and calculate comparable audit metrics."""

from __future__ import annotations

import argparse
import json
import re
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


COUNT_FIELDS = (
    "sent",
    "delivered",
    "unique_opens",
    "unique_clickers",
    "unsubscribes",
    "complaints",
    "sessions",
    "engaged_sessions",
    "leads",
    "qualified_leads",
    "sales",
)
SOURCE_NAMES = (
    "unisender",
    "link_stats",
    "utm",
    "web_analytics",
    "web_analytics_comparison",
    "crm",
    "resend_dedup",
)
SOURCE_STATUSES = {"complete", "partial", "missing", "not_applicable"}
LINK_COUNT_FIELDS = (
    "all_clicks",
    "unique_clickers",
    "sessions",
    "engaged_sessions",
    "leads",
    "qualified_leads",
    "sales",
)
PII_QUERY_KEYS = {"email", "e-mail", "mail", "phone", "telephone", "tel", "name", "first_name", "last_name", "fio"}
EMAIL_VALUE_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def ratio(numerator: Any, denominator: Any) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def median(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return statistics.median(clean) if clean else None


def validate_campaign(campaign: dict[str, Any], index: int) -> list[str]:
    errors: list[str] = []
    prefix = f"campaigns[{index}]"
    if not campaign.get("campaign_id"):
        errors.append(f"{prefix}.campaign_id is required")
    if campaign.get("campaign_type") not in {"primary", "resend", "excluded"}:
        errors.append(f"{prefix}.campaign_type must be primary, resend, or excluded")
    if campaign.get("campaign_type") == "resend" and not campaign.get("original_campaign_id"):
        errors.append(f"{prefix}.original_campaign_id is required for resend")
    if not campaign.get("sent_at"):
        errors.append(f"{prefix}.sent_at is required")
    else:
        try:
            parse_datetime(campaign["sent_at"])
        except (TypeError, ValueError):
            errors.append(f"{prefix}.sent_at must be ISO 8601")
    if not campaign.get("observation_window"):
        errors.append(f"{prefix}.observation_window is required")

    for field in COUNT_FIELDS:
        value = campaign.get(field)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
            errors.append(f"{prefix}.{field} must be a non-negative integer or null")

    revenue = campaign.get("revenue")
    if revenue is not None and (not isinstance(revenue, (int, float)) or isinstance(revenue, bool) or revenue < 0):
        errors.append(f"{prefix}.revenue must be a non-negative number or null")

    sent = campaign.get("sent")
    delivered = campaign.get("delivered")
    if sent is not None and delivered is not None and delivered > sent:
        errors.append(f"{prefix}.delivered cannot exceed sent")
    for field in ("unique_opens", "unique_clickers", "unsubscribes", "complaints"):
        value = campaign.get(field)
        if delivered is not None and value is not None and value > delivered:
            errors.append(f"{prefix}.{field} cannot exceed delivered")
    sessions = campaign.get("sessions")
    engaged = campaign.get("engaged_sessions")
    if sessions is not None and engaged is not None and engaged > sessions:
        errors.append(f"{prefix}.engaged_sessions cannot exceed sessions")
    leads = campaign.get("leads")
    qualified = campaign.get("qualified_leads")
    sales = campaign.get("sales")
    if leads is not None and qualified is not None and qualified > leads:
        errors.append(f"{prefix}.qualified_leads cannot exceed leads")
    if leads is not None and sales is not None and sales > leads:
        errors.append(f"{prefix}.sales cannot exceed leads")

    source_status = campaign.get("source_status")
    if not isinstance(source_status, dict):
        errors.append(f"{prefix}.source_status must be an object")
        source_status = {}
    for source in SOURCE_NAMES:
        if source_status.get(source) not in SOURCE_STATUSES:
            errors.append(
                f"{prefix}.source_status.{source} must be complete, partial, missing, or not_applicable"
            )
        if (
            campaign.get("campaign_type") != "excluded"
            and source != "resend_dedup"
            and source_status.get(source) == "not_applicable"
        ):
            errors.append(f"{prefix}.source_status.{source} cannot be not_applicable")

    if source_status.get("unisender") == "complete":
        for field in ("sent", "delivered", "unique_opens", "unique_clickers", "unsubscribes", "complaints"):
            if campaign.get(field) is None:
                errors.append(f"{prefix}.{field} is required when unisender is complete")

    if source_status.get("web_analytics") == "complete" and campaign.get("web_analytics_source") not in {
        "metrika",
        "matomo",
    }:
        errors.append(f"{prefix}.web_analytics_source must be metrika or matomo when web_analytics is complete")
    if source_status.get("web_analytics") == "complete":
        for field in ("sessions", "engaged_sessions"):
            if campaign.get(field) is None:
                errors.append(f"{prefix}.{field} is required when web_analytics is complete")
    if source_status.get("web_analytics_comparison") == "complete":
        comparison_source = campaign.get("web_analytics_comparison_source")
        if comparison_source not in {"metrika", "matomo"}:
            errors.append(
                f"{prefix}.web_analytics_comparison_source must be metrika or matomo when comparison is complete"
            )
        if comparison_source == campaign.get("web_analytics_source"):
            errors.append(f"{prefix}.web_analytics_comparison_source must differ from web_analytics_source")
        comparison_metrics = campaign.get("web_analytics_comparison_metrics")
        if not isinstance(comparison_metrics, dict):
            errors.append(f"{prefix}.web_analytics_comparison_metrics must be an object when comparison is complete")
        else:
            for field in ("sessions", "engaged_sessions"):
                value = comparison_metrics.get(field)
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    errors.append(f"{prefix}.web_analytics_comparison_metrics.{field} must be a non-negative integer")
            if (
                isinstance(comparison_metrics.get("sessions"), int)
                and isinstance(comparison_metrics.get("engaged_sessions"), int)
                and comparison_metrics["engaged_sessions"] > comparison_metrics["sessions"]
            ):
                errors.append(f"{prefix}.web_analytics_comparison_metrics.engaged_sessions cannot exceed sessions")
    if campaign.get("link_unique_clickers_status") not in {"available", "unavailable", "partial"}:
        errors.append(f"{prefix}.link_unique_clickers_status must be available, unavailable, or partial")

    links = campaign.get("links")
    if not isinstance(links, list):
        errors.append(f"{prefix}.links must be an array")
        links = []
    if source_status.get("link_stats") == "complete" and not links:
        errors.append(f"{prefix}.links cannot be empty when link_stats is complete")
    if source_status.get("link_stats") == "complete":
        expected_link_count = campaign.get("expected_link_count")
        if not isinstance(expected_link_count, int) or isinstance(expected_link_count, bool) or expected_link_count < 1:
            errors.append(f"{prefix}.expected_link_count must be a positive integer when link_stats is complete")
        elif expected_link_count != len(links):
            errors.append(f"{prefix}.expected_link_count must equal the number of links")
    utm_contents: list[str] = []
    for link_index, link in enumerate(links):
        link_prefix = f"{prefix}.links[{link_index}]"
        if not isinstance(link, dict):
            errors.append(f"{link_prefix} must be an object")
            continue
        utm_content = link.get("utm_content")
        if source_status.get("utm") == "complete" and not utm_content:
            errors.append(f"{link_prefix}.utm_content is required when utm is complete")
        if utm_content:
            utm_contents.append(str(utm_content))
        url = link.get("url")
        if not isinstance(url, str) or not url:
            if source_status.get("utm") == "complete":
                errors.append(f"{link_prefix}.url is required when utm is complete")
            elif url is not None and not isinstance(url, str):
                errors.append(f"{link_prefix}.url must be a string or null")
        else:
            try:
                raw_query = urlparse(url).query
                query = parse_qs(raw_query, keep_blank_values=True)
                # Some consumers also treat semicolons as query separators.
                privacy_query = parse_qs(raw_query.replace(";", "&"), keep_blank_values=True)
            except ValueError:
                errors.append(f"{link_prefix}.url must be a valid URL")
            else:
                for query_key, query_values in privacy_query.items():
                    if query_key.lower() in PII_QUERY_KEYS:
                        errors.append(f"{link_prefix}.url contains prohibited PII query key: {query_key}")
                    if EMAIL_VALUE_PATTERN.search(query_key):
                        errors.append(f"{link_prefix}.url contains an email-like query key")
                    if any(EMAIL_VALUE_PATTERN.search(value) for value in query_values):
                        errors.append(f"{link_prefix}.url contains an email-like query value")
                if source_status.get("utm") == "complete":
                    expected = {
                        "utm_source": "unisender",
                        "utm_medium": "email",
                        "utm_campaign": campaign.get("utm_campaign"),
                        "utm_content": utm_content,
                    }
                    for parameter, expected_value in expected.items():
                        actual = query.get(parameter, [None])[0]
                        if not expected_value or actual != str(expected_value):
                            errors.append(
                                f"{link_prefix}.url must contain {parameter}={expected_value} when utm is complete"
                            )
        for field in LINK_COUNT_FIELDS:
            value = link.get(field)
            if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
                errors.append(f"{link_prefix}.{field} must be a non-negative integer or null")
        if source_status.get("link_stats") == "complete" and link.get("all_clicks") is None:
            errors.append(f"{link_prefix}.all_clicks is required when link_stats is complete")
        link_sessions = link.get("sessions")
        link_engaged = link.get("engaged_sessions")
        if link_sessions is not None and link_engaged is not None and link_engaged > link_sessions:
            errors.append(f"{link_prefix}.engaged_sessions cannot exceed sessions")
        link_leads = link.get("leads")
        link_qualified = link.get("qualified_leads")
        link_sales = link.get("sales")
        if link_leads is not None and link_qualified is not None and link_qualified > link_leads:
            errors.append(f"{link_prefix}.qualified_leads cannot exceed leads")
        if link_leads is not None and link_sales is not None and link_sales > link_leads:
            errors.append(f"{link_prefix}.sales cannot exceed leads")
        link_revenue = link.get("revenue")
        if link_revenue is not None and (
            not isinstance(link_revenue, (int, float)) or isinstance(link_revenue, bool) or link_revenue < 0
        ):
            errors.append(f"{link_prefix}.revenue must be a non-negative number or null")
    if source_status.get("utm") == "complete" and len(utm_contents) != len(set(utm_contents)):
        errors.append(f"{prefix}.links must have unique utm_content values when utm is complete")
    if source_status.get("link_stats") == "complete":
        link_map_total_clicks = campaign.get("link_map_total_clicks")
        if not isinstance(link_map_total_clicks, int) or isinstance(link_map_total_clicks, bool) or link_map_total_clicks < 0:
            errors.append(f"{prefix}.link_map_total_clicks must be a non-negative integer when link_stats is complete")
        elif sum(link.get("all_clicks", 0) for link in links if isinstance(link, dict)) != link_map_total_clicks:
            errors.append(f"{prefix}.link_map_total_clicks must equal the sum of links[].all_clicks")
    link_unique_status = campaign.get("link_unique_clickers_status")
    link_unique_values = [link.get("unique_clickers") for link in links if isinstance(link, dict)]
    if link_unique_status == "available" and any(value is None for value in link_unique_values):
        errors.append(f"{prefix}.links[].unique_clickers is required when link unique clickers are available")
    if link_unique_status == "unavailable" and any(value is not None for value in link_unique_values):
        errors.append(f"{prefix}.links[].unique_clickers must be null when link unique clickers are unavailable")
    if source_status.get("crm") == "complete":
        if not campaign.get("crm_source"):
            errors.append(f"{prefix}.crm_source is required when crm is complete")
        for field in ("leads", "qualified_leads", "sales", "revenue"):
            if campaign.get(field) is None:
                errors.append(f"{prefix}.{field} is required when crm is complete")
    if campaign.get("campaign_type") == "primary" and source_status.get("resend_dedup") != "not_applicable":
        errors.append(f"{prefix}.source_status.resend_dedup must be not_applicable for primary")
    if campaign.get("campaign_type") == "resend" and source_status.get("resend_dedup") == "complete":
        pair_metrics = campaign.get("resend_pair_metrics")
        if not isinstance(pair_metrics, dict) or not pair_metrics:
            errors.append(f"{prefix}.resend_pair_metrics is required when resend_dedup is complete")
        else:
            required_pair_fields = (
                "incremental_unique_openers",
                "incremental_unique_clickers",
                "incremental_sessions",
                "incremental_leads",
                "deduplicated_unique_openers",
                "deduplicated_unique_clickers",
            )
            for field in required_pair_fields:
                value = pair_metrics.get(field)
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    errors.append(f"{prefix}.resend_pair_metrics.{field} must be a non-negative integer")
    if campaign.get("campaign_type") == "resend" and source_status.get("resend_dedup") == "not_applicable":
        errors.append(f"{prefix}.source_status.resend_dedup cannot be not_applicable for resend")
    return errors


def campaign_metrics(campaign: dict[str, Any], as_of: datetime, maturity_days: int) -> dict[str, Any]:
    sent_at = parse_datetime(campaign["sent_at"])
    if sent_at.tzinfo is None and as_of.tzinfo is not None:
        sent_at = sent_at.replace(tzinfo=as_of.tzinfo)
    if sent_at.tzinfo is not None and as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=sent_at.tzinfo)
    age_days = max(0.0, (as_of - sent_at).total_seconds() / 86400)
    delivered = campaign.get("delivered")
    unique_opens = campaign.get("unique_opens")
    unique_clickers = campaign.get("unique_clickers")
    sessions = campaign.get("sessions")
    leads = campaign.get("leads")
    sales = campaign.get("sales")
    revenue = campaign.get("revenue")
    metrics = {
        "delivery_rate": ratio(delivered, campaign.get("sent")),
        "open_rate": ratio(unique_opens, delivered),
        "ctr": ratio(unique_clickers, delivered),
        "ctor": ratio(unique_clickers, unique_opens),
        "unsubscribe_rate": ratio(campaign.get("unsubscribes"), delivered),
        "complaint_rate": ratio(campaign.get("complaints"), delivered),
        "sessions_per_clicker": ratio(sessions, unique_clickers),
        "engaged_rate": ratio(campaign.get("engaged_sessions"), sessions),
        "lead_cr": ratio(leads, sessions),
        "leads_per_1000_delivered": None if ratio(leads, delivered) is None else ratio(leads, delivered) * 1000,
        "sales_cr": ratio(sales, leads),
        "revenue_per_1000_delivered": (
            None if ratio(revenue, delivered) is None else ratio(revenue, delivered) * 1000
        ),
    }
    eligible = bool(
        campaign.get("campaign_type") == "primary"
        and campaign.get("comparable", True)
        and campaign.get("source_status", {}).get("unisender") == "complete"
        and campaign.get("observation_window") == f"D+{maturity_days}"
        and age_days >= maturity_days
    )
    return {**campaign, "age_days": round(age_days, 3), "baseline_eligible": eligible, "metrics": metrics}


def weighted_baseline(campaigns: list[dict[str, Any]]) -> dict[str, Any]:
    def total(field: str) -> int | float | None:
        # A missing campaign value makes the aggregate unknown. Summing a partial
        # numerator against a complete denominator would fabricate a weighted rate.
        values = [campaign.get(field) for campaign in campaigns]
        return sum(values) if values and all(value is not None for value in values) else None

    totals = {field: total(field) for field in COUNT_FIELDS}
    totals["revenue"] = total("revenue")
    delivered = totals["delivered"]
    opens = totals["unique_opens"]
    clickers = totals["unique_clickers"]
    sessions = totals["sessions"]
    leads = totals["leads"]
    sales = totals["sales"]
    revenue = totals["revenue"]
    weighted = {
        "delivery_rate": ratio(delivered, totals["sent"]),
        "open_rate": ratio(opens, delivered),
        "ctr": ratio(clickers, delivered),
        "ctor": ratio(clickers, opens),
        "unsubscribe_rate": ratio(totals["unsubscribes"], delivered),
        "complaint_rate": ratio(totals["complaints"], delivered),
        "sessions_per_clicker": ratio(sessions, clickers),
        "engaged_rate": ratio(totals["engaged_sessions"], sessions),
        "lead_cr": ratio(leads, sessions),
        "leads_per_1000_delivered": None if ratio(leads, delivered) is None else ratio(leads, delivered) * 1000,
        "sales_cr": ratio(sales, leads),
        "revenue_per_1000_delivered": (
            None if ratio(revenue, delivered) is None else ratio(revenue, delivered) * 1000
        ),
    }
    medians = {
        field: median([campaign["metrics"][field] for campaign in campaigns])
        for field in weighted
    }
    return {"campaign_count": len(campaigns), "totals": totals, "weighted_rates": weighted, "median_campaign_rates": medians}


def calculate(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload.get("campaigns"), list):
        raise ValueError("campaigns must be an array")
    try:
        as_of = parse_datetime(payload["as_of"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("as_of must be a valid ISO 8601 timestamp") from exc
    maturity_days = payload.get("maturity_days", 7)
    if not isinstance(maturity_days, int) or isinstance(maturity_days, bool) or maturity_days < 1:
        raise ValueError("maturity_days must be a positive integer")
    required_sources = payload.get("required_sources", list(SOURCE_NAMES))
    if (
        not isinstance(required_sources, list)
        or not required_sources
        or any(source not in SOURCE_NAMES for source in required_sources)
    ):
        raise ValueError(f"required_sources must be a non-empty array using: {', '.join(SOURCE_NAMES)}")

    errors: list[str] = []
    seen_snapshots: set[tuple[str, str]] = set()
    for index, campaign in enumerate(payload["campaigns"]):
        if not isinstance(campaign, dict):
            errors.append(f"campaigns[{index}] must be an object")
            continue
        errors.extend(validate_campaign(campaign, index))
        snapshot_key = (str(campaign.get("campaign_id")), str(campaign.get("observation_window")))
        if snapshot_key in seen_snapshots:
            errors.append(
                f"campaigns[{index}] duplicates campaign_id + observation_window: "
                f"{snapshot_key[0]} + {snapshot_key[1]}"
            )
        seen_snapshots.add(snapshot_key)
    if errors:
        raise ValueError("; ".join(errors))

    primary_by_id = {
        str(campaign["campaign_id"]): campaign
        for campaign in payload["campaigns"]
        if campaign.get("campaign_type") == "primary"
    }
    missing_originals = [
        str(campaign["original_campaign_id"])
        for campaign in payload["campaigns"]
        if campaign.get("campaign_type") == "resend"
        and str(campaign.get("original_campaign_id")) not in primary_by_id
    ]
    if missing_originals:
        raise ValueError(f"resend original_campaign_id must reference an input primary campaign: {missing_originals}")

    pair_errors: list[str] = []
    for campaign in payload["campaigns"]:
        if campaign.get("campaign_type") != "resend":
            continue
        original = primary_by_id[str(campaign["original_campaign_id"])]
        if parse_datetime(campaign["sent_at"]) <= parse_datetime(original["sent_at"]):
            pair_errors.append(f"resend {campaign['campaign_id']} must be sent after original {original['campaign_id']}")
        if campaign.get("source_status", {}).get("resend_dedup") != "complete":
            continue
        pair = campaign["resend_pair_metrics"]
        bounds = {
            "incremental_unique_openers": campaign.get("unique_opens"),
            "incremental_unique_clickers": campaign.get("unique_clickers"),
            "incremental_sessions": campaign.get("sessions"),
            "incremental_leads": campaign.get("leads"),
        }
        for field, upper_bound in bounds.items():
            if upper_bound is None or pair[field] > upper_bound:
                pair_errors.append(
                    f"resend {campaign['campaign_id']} {field} cannot exceed the corresponding resend metric"
                )
        expected_openers = original.get("unique_opens")
        expected_clickers = original.get("unique_clickers")
        if expected_openers is None or pair["deduplicated_unique_openers"] != expected_openers + pair["incremental_unique_openers"]:
            pair_errors.append(
                f"resend {campaign['campaign_id']} deduplicated_unique_openers must equal original unique_opens + incremental_unique_openers"
            )
        if expected_clickers is None or pair["deduplicated_unique_clickers"] != expected_clickers + pair["incremental_unique_clickers"]:
            pair_errors.append(
                f"resend {campaign['campaign_id']} deduplicated_unique_clickers must equal original unique_clickers + incremental_unique_clickers"
            )
        pair_delivered = (original.get("delivered") or 0) + (campaign.get("delivered") or 0)
        if pair["deduplicated_unique_openers"] > pair_delivered:
            pair_errors.append(f"resend {campaign['campaign_id']} deduplicated_unique_openers exceeds pair delivery")
        if pair["deduplicated_unique_clickers"] > pair_delivered:
            pair_errors.append(f"resend {campaign['campaign_id']} deduplicated_unique_clickers exceeds pair delivery")
    if pair_errors:
        raise ValueError("; ".join(pair_errors))

    enriched = [campaign_metrics(campaign, as_of, maturity_days) for campaign in payload["campaigns"]]
    eligible = [campaign for campaign in enriched if campaign["baseline_eligible"]]
    in_scope = [
        campaign
        for campaign in enriched
        if campaign["campaign_type"] != "excluded"
        and campaign.get("observation_window") == f"D+{maturity_days}"
        and campaign["age_days"] >= maturity_days
    ]
    source_gaps = [
        {
            "campaign_id": campaign["campaign_id"],
            "source": source,
            "status": campaign.get("source_status", {}).get(source, "missing"),
        }
        for campaign in in_scope
        for source in required_sources
        if not (
            campaign.get("source_status", {}).get(source) == "complete"
            or (
                source == "resend_dedup"
                and campaign["campaign_type"] == "primary"
                and campaign.get("source_status", {}).get(source) == "not_applicable"
            )
        )
    ]
    status = "complete" if eligible and in_scope and not source_gaps else "partial"
    return {
        "status": status,
        "as_of": payload["as_of"],
        "maturity_days": maturity_days,
        "required_sources": required_sources,
        "source_gaps": source_gaps,
        "counts": {
            "all": len(enriched),
            "primary": sum(c["campaign_type"] == "primary" for c in enriched),
            "resend": sum(c["campaign_type"] == "resend" for c in enriched),
            "excluded": sum(c["campaign_type"] == "excluded" for c in enriched),
            "baseline_eligible": len(eligible),
        },
        "baseline": weighted_baseline(eligible),
        "campaigns": enriched,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Normalized campaign JSON")
    parser.add_argument("--output", type=Path, help="Write result to this JSON file")
    args = parser.parse_args()
    with args.input.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    result = calculate(payload)
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
