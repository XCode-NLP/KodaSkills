#!/usr/bin/env python3
"""Call Yandex SpeechKit synchronous REST recognition."""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from env_config import load_project_env


load_project_env()


SYNC_ENDPOINT = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"


def build_auth_header(args: argparse.Namespace) -> str:
    if args.iam_token:
        return f"Bearer {args.iam_token}"
    if args.api_key:
        return f"Api-Key {args.api_key}"
    env_iam = os.getenv("YANDEX_IAM_TOKEN") or os.getenv("IAM_TOKEN")
    if env_iam:
        return f"Bearer {env_iam}"
    env_api_key = os.getenv("YANDEX_API_KEY") or os.getenv("API_KEY")
    if env_api_key:
        return f"Api-Key {env_api_key}"
    raise SystemExit("No API key or IAM token provided. Use flags or env vars.")


def format_request_error(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        body = exc.read().decode("utf-8", errors="replace").strip()
        detail = f": {body}" if body else ""
        message = f"SpeechKit request failed with HTTP {exc.code} {exc.reason}{detail}"
        if exc.code == 403:
            message += (
                "\nPermissionDenied diagnostics:"
                "\n- check that the service account or principal has SpeechKit permissions;"
                "\n- check YANDEX_FOLDER_ID / --folder-id and make sure it points to the intended folder;"
                "\n- try --iam-token instead of --api-key for SpeechKit;"
                "\n- check that the key/token belongs to the expected cloud and folder."
            )
        return message
    if isinstance(exc, urllib.error.URLError):
        reason = exc.reason
        if isinstance(reason, ssl.SSLCertVerificationError):
            return (
                "SpeechKit request failed due to TLS certificate verification. "
                "Your local Python trust store appears incomplete."
            )
        return f"SpeechKit request failed: {reason}"
    return f"SpeechKit request failed: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio_file", help="Path to a local audio file")
    parser.add_argument("--lang", default="ru-RU", help="Recognition language")
    parser.add_argument("--topic", default="general", help="Recognition model/topic")
    parser.add_argument("--folder-id", help="Folder ID when required by your auth flow")
    parser.add_argument("--format", default=None, help="Audio format query parameter when needed")
    parser.add_argument("--sample-rate-hertz", type=int, default=None, help="Sample rate query parameter")
    parser.add_argument("--profanity-filter", action="store_true", help="Enable profanity filter")
    parser.add_argument("--raw-results", action="store_true", help="Print raw JSON instead of transcript text only")
    parser.add_argument("--api-key", help="Yandex API key")
    parser.add_argument("--iam-token", help="Yandex IAM token")
    parser.add_argument("--retries", type=int, default=3, help="Attempts for transient network failures")
    parser.add_argument("--retry-backoff", type=float, default=2.0, help="Initial retry backoff in seconds")
    parser.add_argument("--request-timeout", type=float, default=120.0, help="HTTP request timeout in seconds")
    args = parser.parse_args()

    audio_path = Path(args.audio_file).expanduser().resolve()
    if not audio_path.is_file():
        raise SystemExit(f"Audio file not found: {audio_path}")

    query = {
        "lang": args.lang,
        "topic": args.topic,
    }
    folder_id = args.folder_id or os.getenv("YANDEX_FOLDER_ID")
    if folder_id:
        query["folderId"] = folder_id
    if args.format:
        query["format"] = args.format
    if args.sample_rate_hertz is not None:
        query["sampleRateHertz"] = str(args.sample_rate_hertz)
    if args.profanity_filter:
        query["profanityFilter"] = "true"

    url = f"{SYNC_ENDPOINT}?{urllib.parse.urlencode(query)}"
    headers = {
        "Authorization": build_auth_header(args),
        "Content-Type": "application/octet-stream",
    }
    body = audio_path.read_bytes()

    payload = None
    last_error: BaseException | None = None
    for attempt in range(1, max(args.retries, 1) + 1):
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=args.request_timeout) as response:
                payload = json.load(response)
            break
        except urllib.error.HTTPError as exc:
            raise SystemExit(format_request_error(exc)) from exc
        except (BrokenPipeError, TimeoutError, OSError, urllib.error.URLError) as exc:
            last_error = exc
            if attempt >= max(args.retries, 1):
                raise SystemExit(
                    f"SpeechKit sync request failed after {attempt} attempts: {format_request_error(exc)}"
                ) from exc
            time.sleep(args.retry_backoff * (2 ** (attempt - 1)))

    if payload is None:
        raise SystemExit(f"SpeechKit sync request failed: {last_error}")

    if args.raw_results:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        print(payload.get("result", ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
