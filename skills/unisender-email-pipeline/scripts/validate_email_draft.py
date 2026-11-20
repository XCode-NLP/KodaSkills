#!/usr/bin/env python3
"""Validate a profile-configured email draft before creating a UniSender message."""

from __future__ import annotations

import argparse
import json
import posixpath
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit


PLACEHOLDER_RE = re.compile(r"\{\{[^{}]+\}\}|\bTODO\b|example\.com", re.IGNORECASE)
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
GENERAL_PATHS = {"/", "/news", "/blog", "/articles", "/category", "/tag", "/search"}
REQUIRED_COLOR_ROLES = ("background", "paper", "text", "paragraph", "muted", "accent", "dark", "light")


class DraftParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self.duplicate_link_attributes = False
        self.article_cards = 0
        self.images: list[dict[str, str]] = []
        self.has_group = False
        self.has_block = False
        self.tr_roles: list[bool] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            names = [key.lower() for key, _ in attrs]
            if any(names.count(key) > 1 for key in ("href", "data-tracking")):
                self.duplicate_link_attributes = True
        values = {key.lower(): value or "" for key, value in attrs}
        if values.get("em") == "group":
            self.has_group = True
        if values.get("em") == "block":
            self.has_block = True
        if tag.lower() == "tr":
            self.tr_roles.append(values.get("data-role") == "article-card")
        if values.get("data-role") == "article-card":
            self.article_cards += 1
        if tag.lower() == "a" and "href" in values:
            self.links.append(
                {
                    "href": values["href"],
                    "tracking": values.get("data-tracking", "content"),
                    "material": any(self.tr_roles),
                }
            )
        if tag.lower() == "img":
            self.images.append({"src": values.get("src", ""), "alt": values.get("alt", "")})

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "tr" and self.tr_roles:
            self.tr_roles.pop()


def error(errors: list[str], message: str) -> None:
    if message not in errors:
        errors.append(message)


def validate(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    subject = payload.get("subject")
    preheader = payload.get("preheader")
    campaign = payload.get("utm_campaign")
    html = payload.get("html")
    expected_articles = payload.get("expected_articles")

    if not isinstance(subject, str) or not subject.strip():
        error(errors, "subject is required")
    elif len(subject.strip()) > 50:
        error(errors, "subject must be at most 50 characters")
    if not isinstance(preheader, str) or not preheader.strip():
        error(errors, "preheader is required")
    elif not 70 <= len(preheader.strip()) <= 110:
        error(errors, "preheader must be 70–110 characters")
    if not isinstance(campaign, str) or not campaign:
        error(errors, "utm_campaign is required")
    if not isinstance(expected_articles, int) or isinstance(expected_articles, bool):
        error(errors, "expected_articles must be an integer")
    elif not 3 <= expected_articles <= 5:
        error(errors, "expected_articles must be between 3 and 5")
    if not isinstance(html, str) or not html.strip():
        error(errors, "html is required")
        html = ""

    if PLACEHOLDER_RE.search(html):
        error(errors, "HTML contains a placeholder, TODO or example.com")
    lower = html.lower()
    if "<!doctype html" not in lower:
        error(errors, "HTML must contain a doctype")
    if "<script" in lower or "javascript:" in lower:
        error(errors, "JavaScript is prohibited")
    if "display:flex" in lower or "display: flex" in lower:
        error(errors, "Flexbox is prohibited")
    if "display:grid" in lower or "display: grid" in lower:
        error(errors, "CSS Grid is prohibited")
    if "max-width:600px" not in lower and "max-width: 600px" not in lower:
        error(errors, "HTML must use a 600 px responsive container")
    profile = payload.get("brand_profile")
    if not isinstance(profile, dict):
        error(errors, "brand_profile is required; do not invent a business identity")
        profile = {}
    for field in ("brand_name", "sender_name", "font_family"):
        value = profile.get(field)
        if not isinstance(value, str) or not value.strip():
            error(errors, f"brand_profile.{field} is required")
        elif value.casefold() not in html.casefold():
            error(errors, f"HTML must preserve configured {field}")
    colors = profile.get("colors")
    if not isinstance(colors, dict):
        error(errors, "brand_profile.colors is required")
        colors = {}
    for role in REQUIRED_COLOR_ROLES:
        token = colors.get(role)
        if not isinstance(token, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", token):
            error(errors, f"brand_profile.colors.{role} must be a six-digit hex color")
        elif token.lower() not in lower:
            error(errors, f"HTML must preserve configured color role {role}")
    labels = profile.get("required_labels", [])
    if not isinstance(labels, list) or any(not isinstance(x, str) or not x.strip() for x in labels):
        error(errors, "brand_profile.required_labels must be non-empty strings")
    else:
        for label in labels:
            if label not in html:
                error(errors, f"HTML must preserve configured label: {label}")
    if preheader and isinstance(preheader, str) and preheader not in html:
        error(errors, "preheader text is not embedded in HTML")

    parser = DraftParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception as exc:
        error(errors, f"HTML parser failed: {exc}")

    if parser.duplicate_link_attributes:
        error(errors, "links must not contain duplicate href or data-tracking attributes")
    if not parser.has_group:
        error(errors, 'HTML must preserve em="group"')
    if not parser.has_block:
        error(errors, 'HTML must preserve em="block"')
    if isinstance(expected_articles, int) and parser.article_cards != expected_articles:
        error(
            errors,
            f"article card count {parser.article_cards} does not match expected_articles {expected_articles}",
        )

    seen_utm_content: set[str] = set()
    checked_links = 0
    for index, item in enumerate(parser.links):
        href = item["href"].strip()
        tracking = item["tracking"]
        prefix = f"link[{index}]"
        if not href or href == "#" or PLACEHOLDER_RE.search(href):
            error(errors, f"{prefix} is empty or placeholder")
            continue
        if href.startswith(("mailto:", "tel:")):
            if tracking != "operational":
                warnings.append(f"{prefix} is mailto/tel and should be marked operational")
            continue
        parts = urlsplit(href)
        if parts.scheme != "https" or not parts.netloc or parts.username or parts.password:
            error(errors, f"{prefix} must be absolute HTTPS")
            continue
        host = parts.netloc.lower().removeprefix("www.")
        if item["material"] and ((posixpath.normpath(parts.path).rstrip("/") or "/") in GENERAL_PATHS or re.search(r"/(category|tag|search)(/|$)", parts.path)):
            error(errors, f"{prefix} points to a general section instead of a material")
        query = parse_qs(parts.query)
        privacy_query = parse_qs(parts.query.replace(";", "&"), keep_blank_values=True)
        for key, values in privacy_query.items():
            if EMAIL_RE.search(key):
                error(errors, f"{prefix} contains an email-like query key")
            if key.lower() in PII_KEYS:
                error(errors, f"{prefix} contains prohibited PII key: {key}")
            if any(EMAIL_RE.search(value) for value in values):
                error(errors, f"{prefix} contains an email-like query value")
        if query.get("utm_source", [None])[0] == "chatgpt.com":
            error(errors, f"{prefix} contains utm_source=chatgpt.com")
        if tracking == "operational":
            continue
        expected = {
            "utm_source": "unisender",
            "utm_medium": "email",
            "utm_campaign": campaign,
        }
        for key, expected_value in expected.items():
            actual = query.get(key, [None])[0]
            if actual != expected_value:
                error(errors, f"{prefix} must contain {key}={expected_value}")
        utm_content = query.get("utm_content", [None])[0]
        if not utm_content:
            error(errors, f"{prefix} must contain utm_content")
        elif utm_content in seen_utm_content:
            error(errors, f"{prefix} duplicates utm_content={utm_content}")
        else:
            seen_utm_content.add(utm_content)
        checked_links += 1

    if checked_links == 0:
        error(errors, "HTML has no tracked content links")

    for index, image in enumerate(parser.images):
        if not image["src"]:
            error(errors, f"image[{index}] has no src")
        else:
            image_parts = urlsplit(image["src"])
            if image_parts.scheme != "https" or not image_parts.netloc or image_parts.username or image_parts.password:
                error(errors, f"image[{index}] must use an absolute HTTPS URL without credentials")
        if not image["alt"].strip():
            error(errors, f"image[{index}] has no alt text")

    warnings.append("Verify the UniSender system unsubscribe link in Browser preview after draft creation")
    return {
        "status": "blocked" if errors else "passed",
        "errors": errors,
        "warnings": warnings,
        "article_cards": parser.article_cards,
        "tracked_links": checked_links,
        "images": len(parser.images),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Draft JSON with subject, preheader, utm_campaign and html")
    parser.add_argument("--output", type=Path, help="Optional result JSON path")
    args = parser.parse_args()
    with args.input.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    result = validate(payload)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if result["status"] == "blocked":
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
