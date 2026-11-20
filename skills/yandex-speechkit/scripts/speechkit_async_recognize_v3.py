#!/usr/bin/env python3
"""Submit, poll, and fetch Yandex SpeechKit STT v3 async recognition."""

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
from typing import Any

from env_config import load_project_env


load_project_env()


SUBMIT_ENDPOINT = "https://stt.api.cloud.yandex.net/stt/v3/recognizeFileAsync"
RESULT_ENDPOINT = "https://stt.api.cloud.yandex.net/stt/v3/getRecognition"
OPERATION_ENDPOINT = "https://operation.api.cloud.yandex.net/operations"


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


def build_headers(args: argparse.Namespace) -> dict[str, str]:
    headers = {
        "Authorization": build_auth_header(args),
        "Content-Type": "application/json",
    }
    folder_id = args.folder_id or os.getenv("YANDEX_FOLDER_ID")
    if folder_id:
        headers["x-folder-id"] = folder_id
    return headers


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
                "\n- try --iam-token instead of --api-key for SpeechKit STT v3 async;"
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


def request_json(
    url: str,
    *,
    headers: dict[str, str],
    body: dict | None = None,
    method: str = "GET",
    timeout: float = 60.0,
) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = response.read().decode("utf-8", errors="replace").strip()
            if not payload:
                return {}
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                entries: list[dict[str, Any]] = []
                decoder = json.JSONDecoder()
                index = 0
                length = len(payload)
                while index < length:
                    while index < length and payload[index].isspace():
                        index += 1
                    if index >= length:
                        break
                    item, next_index = decoder.raw_decode(payload, index)
                    if isinstance(item, dict):
                        entries.append(item)
                    index = next_index
                if not entries:
                    raise SystemExit(f"SpeechKit returned non-JSON response: {payload[:500]}")
                return {"entries": entries}
            return parsed if isinstance(parsed, dict) else {"value": parsed}
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise SystemExit(format_request_error(exc)) from exc


def build_request_body(args: argparse.Namespace) -> dict:
    body: dict[str, object] = {
        "uri": args.uri,
        "recognition_model": {
            "model": args.model,
            "audio_format": {
                "container_audio": {
                    "container_audio_type": args.container_audio_type,
                }
            },
        },
    }
    if args.language_code:
        body["recognition_model"]["language_restriction"] = {
            "restriction_type": "WHITELIST",
            "language_code": [args.language_code],
        }
    return body


def submit_recognition(*, headers: dict[str, str], body: dict[str, object]) -> dict[str, Any]:
    return request_json(SUBMIT_ENDPOINT, headers=headers, body=body, method="POST")


def poll_operation(*, headers: dict[str, str], operation_id: str, poll_interval: float, timeout: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while True:
        operation = request_json(f"{OPERATION_ENDPOINT}/{urllib.parse.quote(operation_id)}", headers=headers)
        if operation.get("done"):
            return operation
        if time.monotonic() >= deadline:
            raise SystemExit("Timed out while waiting for async recognition.")
        time.sleep(poll_interval)


def fetch_result(*, headers: dict[str, str], operation_id: str) -> dict[str, Any]:
    return request_json(
        f"{RESULT_ENDPOINT}?{urllib.parse.urlencode({'operation_id': operation_id})}",
        headers=headers,
    )


def extract_transcript(result: dict[str, Any]) -> str:
    texts: list[str] = []

    def append_from_entry(entry: dict[str, Any]) -> None:
        alternatives = (((entry.get("result") or {}).get("final") or {}).get("alternatives") or [])
        for alt in alternatives:
            if isinstance(alt, dict):
                text = str(alt.get("text", "")).strip()
                if text:
                    texts.append(text)

    if "entries" in result and isinstance(result["entries"], list):
        for entry in result["entries"]:
            if isinstance(entry, dict):
                append_from_entry(entry)
    else:
        append_from_entry(result)

    return "\n".join(texts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uri", help="Object Storage HTTPS URL to the audio file")
    parser.add_argument("--model", default="general", help="Recognition model")
    parser.add_argument(
        "--container-audio-type",
        default="WAV",
        choices=["WAV", "OGG_OPUS", "MP3"],
        help="Container type for recognition_model.audio_format.container_audio.container_audio_type",
    )
    parser.add_argument("--language-code", help="Optional single language code for whitelist restriction")
    parser.add_argument("--folder-id", help="Folder ID. Recommended for service-account flows.")
    parser.add_argument("--api-key", help="Yandex API key")
    parser.add_argument("--iam-token", help="Yandex IAM token")
    parser.add_argument("--poll", action="store_true", help="Poll until the operation is done")
    parser.add_argument("--operation-id", help="Existing async operation id to poll/fetch without submitting")
    parser.add_argument("--fetch-only", action="store_true", help="Only fetch recognition result for --operation-id")
    parser.add_argument("--result-file", help="Optional file path to save fetched raw result JSON")
    parser.add_argument("--transcript-file", help="Optional file path to save extracted transcript")
    parser.add_argument("--poll-interval", type=float, default=5.0, help="Polling interval in seconds")
    parser.add_argument("--timeout", type=float, default=900.0, help="Maximum polling time in seconds")
    parser.add_argument("--raw-results", action="store_true", help="Print full result JSON")
    args = parser.parse_args()

    headers = build_headers(args)
    operation_id = args.operation_id

    if not operation_id:
        if not args.uri:
            raise SystemExit("--uri is required unless --operation-id is provided")
        if args.fetch_only:
            raise SystemExit("--fetch-only requires --operation-id")
        submit_body = build_request_body(args)
        operation = submit_recognition(headers=headers, body=submit_body)
        print(json.dumps({"submitted": operation}, indent=2, ensure_ascii=True))
        operation_id = operation.get("id")
        if not args.poll:
            return 0
        if not operation_id:
            raise SystemExit("Recognition request did not return an operation id.")
    elif args.poll and not args.fetch_only:
        op = poll_operation(
            headers=headers,
            operation_id=str(operation_id),
            poll_interval=args.poll_interval,
            timeout=args.timeout,
        )
        print(json.dumps({"operation": op}, indent=2, ensure_ascii=True))

    result = fetch_result(headers=headers, operation_id=str(operation_id))
    if args.result_file:
        Path(args.result_file).expanduser().resolve().write_text(
            json.dumps(result, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )
    transcript = extract_transcript(result)
    if args.transcript_file:
        Path(args.transcript_file).expanduser().resolve().write_text(
            transcript + ("\n" if transcript else ""),
            encoding="utf-8",
        )
    if args.raw_results:
        print(json.dumps({"result": result}, indent=2, ensure_ascii=True))
    else:
        print(transcript)
    return 0


if __name__ == "__main__":
    sys.exit(main())
