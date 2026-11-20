#!/usr/bin/env python3
"""Generate a private pre-signed download URL for Yandex Object Storage."""

from __future__ import annotations

import argparse
import json
import sys

from object_storage import load_storage_config, object_url, presign_get_url


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", help="Object Storage bucket name")
    parser.add_argument("--object-key", required=True, help="Object key inside the bucket")
    parser.add_argument("--expires-in", type=int, default=24 * 60 * 60, help="TTL in seconds for the private URL")
    parser.add_argument("--public-url", action="store_true", help="Return the plain object URL instead of a private pre-signed URL")
    parser.add_argument("--access-key", help="Static access key")
    parser.add_argument("--secret-key", help="Static secret key")
    parser.add_argument("--endpoint", help="Object Storage endpoint, default: https://storage.yandexcloud.net")
    parser.add_argument("--region", help="Signing region, default: ru-central1")
    args = parser.parse_args()

    config = load_storage_config(
        access_key=args.access_key,
        secret_key=args.secret_key,
        bucket=args.bucket,
        endpoint=args.endpoint,
        region=args.region,
    )
    url = object_url(config, args.object_key) if args.public_url else presign_get_url(
        config,
        args.object_key,
        expires_in=args.expires_in,
    )
    print(
        json.dumps(
            {
                "bucket": config.bucket,
                "key": args.object_key,
                "private": not args.public_url,
                "expires_in": None if args.public_url else args.expires_in,
                "url": url,
            },
            indent=2,
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
