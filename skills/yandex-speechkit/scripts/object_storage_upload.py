#!/usr/bin/env python3
"""Upload a local file to Yandex Object Storage via the S3-compatible API."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from object_storage import load_storage_config, upload_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", help="Local file to upload")
    parser.add_argument("--bucket", help="Object Storage bucket name")
    parser.add_argument("--object-key", required=True, help="Object key inside the bucket")
    parser.add_argument("--content-type", help="Optional content type override")
    parser.add_argument("--access-key", help="Static access key")
    parser.add_argument("--secret-key", help="Static secret key")
    parser.add_argument("--endpoint", help="Object Storage endpoint, default: https://storage.yandexcloud.net")
    parser.add_argument("--region", help="Signing region, default: ru-central1")
    parser.add_argument("--retries", type=int, default=3, help="Attempts for transient upload failures")
    parser.add_argument("--retry-backoff", type=float, default=2.0, help="Initial retry backoff in seconds")
    parser.add_argument("--timeout", type=float, default=120.0, help="HTTP upload timeout in seconds")
    args = parser.parse_args()

    input_path = Path(args.input_file).expanduser().resolve()
    if not input_path.is_file():
        raise SystemExit(f"Input file not found: {input_path}")

    config = load_storage_config(
        access_key=args.access_key,
        secret_key=args.secret_key,
        bucket=args.bucket,
        endpoint=args.endpoint,
        region=args.region,
    )
    payload = upload_file(
        config,
        input_path,
        object_key=args.object_key,
        content_type=args.content_type,
        timeout=args.timeout,
        retries=args.retries,
        retry_backoff=args.retry_backoff,
    )
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
