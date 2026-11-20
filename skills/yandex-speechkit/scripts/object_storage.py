#!/usr/bin/env python3
"""Helpers for Yandex Object Storage uploads and pre-signed URLs."""

from __future__ import annotations

import datetime as dt
import hashlib
import http.client
import hmac
import mimetypes
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from env_config import load_project_env


load_project_env()


DEFAULT_ENDPOINT = "https://storage.yandexcloud.net"
DEFAULT_REGION = "ru-central1"
SERVICE = "s3"
ALGORITHM = "AWS4-HMAC-SHA256"
MAX_PRESIGN_TTL = 30 * 24 * 60 * 60


@dataclass(frozen=True)
class StorageConfig:
    access_key: str
    secret_key: str
    bucket: str
    endpoint: str = DEFAULT_ENDPOINT
    region: str = DEFAULT_REGION


def load_storage_config(
    *,
    access_key: str | None = None,
    secret_key: str | None = None,
    bucket: str | None = None,
    endpoint: str | None = None,
    region: str | None = None,
) -> StorageConfig:
    resolved_access_key = (
        access_key
        or os.getenv("YANDEX_STORAGE_ACCESS_KEY")
        or os.getenv("ACCESS_KEY")
    )
    resolved_secret_key = (
        secret_key
        or os.getenv("YANDEX_STORAGE_SECRET_KEY")
        or os.getenv("SECRET_KEY")
    )
    resolved_bucket = bucket or os.getenv("YANDEX_STORAGE_BUCKET")
    resolved_endpoint = endpoint or os.getenv("YANDEX_STORAGE_ENDPOINT") or DEFAULT_ENDPOINT
    resolved_region = region or os.getenv("YANDEX_STORAGE_REGION") or DEFAULT_REGION

    if not resolved_access_key:
        raise SystemExit("No Object Storage access key provided. Use --access-key or YANDEX_STORAGE_ACCESS_KEY/ACCESS_KEY.")
    if not resolved_secret_key:
        raise SystemExit("No Object Storage secret key provided. Use --secret-key or YANDEX_STORAGE_SECRET_KEY/SECRET_KEY.")
    if not resolved_bucket:
        raise SystemExit("No Object Storage bucket provided. Use --bucket or YANDEX_STORAGE_BUCKET.")

    return StorageConfig(
        access_key=resolved_access_key,
        secret_key=resolved_secret_key,
        bucket=resolved_bucket,
        endpoint=resolved_endpoint.rstrip("/"),
        region=resolved_region,
    )


def guess_content_type(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


def bucket_host(config: StorageConfig) -> str:
    parsed_endpoint = urllib.parse.urlparse(config.endpoint)
    return f"{config.bucket}.{parsed_endpoint.netloc}"


def object_url(config: StorageConfig, object_key: str) -> str:
    quoted_key = quote_object_key(object_key)
    parsed_endpoint = urllib.parse.urlparse(config.endpoint)
    return f"{parsed_endpoint.scheme}://{bucket_host(config)}/{quoted_key}"


def quote_object_key(object_key: str) -> str:
    normalized = object_key.lstrip("/")
    return urllib.parse.quote(normalized, safe="/-_.~")


def hash_payload(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def hash_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sign(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()


def get_signing_key(secret_key: str, datestamp: str, region: str, service: str) -> bytes:
    k_date = sign(("AWS4" + secret_key).encode("utf-8"), datestamp)
    k_region = hmac.new(k_date, region.encode("utf-8"), hashlib.sha256).digest()
    k_service = hmac.new(k_region, service.encode("utf-8"), hashlib.sha256).digest()
    return hmac.new(k_service, b"aws4_request", hashlib.sha256).digest()


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def build_canonical_request(
    method: str,
    canonical_uri: str,
    canonical_querystring: str,
    canonical_headers: str,
    signed_headers: str,
    payload_hash: str,
) -> str:
    return "\n".join(
        [
            method,
            canonical_uri,
            canonical_querystring,
            canonical_headers,
            signed_headers,
            payload_hash,
        ]
    )


def build_string_to_sign(amz_date: str, credential_scope: str, canonical_request: str) -> str:
    canonical_request_hash = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    return "\n".join([ALGORITHM, amz_date, credential_scope, canonical_request_hash])


def upload_file(
    config: StorageConfig,
    file_path: Path,
    *,
    object_key: str,
    content_type: str | None = None,
    timeout: float = 120.0,
    retries: int = 3,
    retry_backoff: float = 2.0,
) -> dict[str, str]:
    if not file_path.is_file():
        raise SystemExit(f"Upload source file not found: {file_path}")

    payload_hash = hash_file(file_path)
    timestamp = now_utc()
    amz_date = timestamp.strftime("%Y%m%dT%H%M%SZ")
    datestamp = timestamp.strftime("%Y%m%d")
    credential_scope = f"{datestamp}/{config.region}/{SERVICE}/aws4_request"

    host = bucket_host(config)
    canonical_uri = f"/{quote_object_key(object_key)}"
    resolved_content_type = content_type or guess_content_type(file_path)
    headers = {
        "content-type": resolved_content_type,
        "host": host,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amz_date,
    }
    signed_headers = ";".join(sorted(headers))
    canonical_headers = "".join(f"{name}:{headers[name]}\n" for name in sorted(headers))
    canonical_request = build_canonical_request(
        "PUT",
        canonical_uri,
        "",
        canonical_headers,
        signed_headers,
        payload_hash,
    )
    string_to_sign = build_string_to_sign(amz_date, credential_scope, canonical_request)
    signing_key = get_signing_key(config.secret_key, datestamp, config.region, SERVICE)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    authorization = (
        f"{ALGORITHM} Credential={config.access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    request_headers = {
        "Authorization": authorization,
        "Content-Type": resolved_content_type,
        "Host": host,
        "X-Amz-Content-SHA256": payload_hash,
        "X-Amz-Date": amz_date,
    }

    last_error: BaseException | None = None
    for attempt in range(1, max(retries, 1) + 1):
        try:
            status, etag = put_file_stream(
                object_url(config, object_key),
                file_path,
                headers=request_headers,
                timeout=timeout,
            )
            break
        except ObjectStorageUploadHTTPError as exc:
            raise SystemExit(str(exc)) from exc
        except (BrokenPipeError, TimeoutError, OSError, urllib.error.URLError) as exc:
            last_error = exc
            if attempt < max(retries, 1):
                time.sleep(retry_backoff * (2 ** (attempt - 1)))
    else:
        curl_status = upload_with_curl(
            object_url(config, object_key),
            file_path,
            headers=request_headers,
            timeout=timeout,
        )
        if curl_status is None:
            put_url = presign_put_url(config, object_key, expires_in=3600)
            curl_status = upload_with_curl(
                put_url,
                file_path,
                headers={"Content-Type": resolved_content_type},
                timeout=timeout,
            )
        if curl_status is None:
            raise SystemExit(
                "Object Storage upload failed after retries and curl fallback. "
                f"Last error: {last_error}. Check network stability, bucket permissions, "
                "Object Storage credentials, and try reusing the prepared file with --skip-prepare."
            )
        status, etag = curl_status, ""

    return {
        "bucket": config.bucket,
        "endpoint": config.endpoint,
        "key": object_key,
        "url": object_url(config, object_key),
        "content_type": resolved_content_type,
        "etag": etag,
        "status": status,
    }


class ObjectStorageUploadHTTPError(RuntimeError):
    pass


def put_file_stream(
    url: str,
    file_path: Path,
    *,
    headers: dict[str, str],
    timeout: float,
    chunk_size: int = 1024 * 1024,
) -> tuple[str, str]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported URL scheme for upload: {parsed.scheme}")

    connection_class = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    connection = connection_class(parsed.netloc, timeout=timeout)
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"

    try:
        connection.putrequest("PUT", path, skip_host=True, skip_accept_encoding=True)
        for name, value in headers.items():
            connection.putheader(name, value)
        connection.putheader("Content-Length", str(file_path.stat().st_size))
        connection.endheaders()
        with file_path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(chunk_size), b""):
                connection.send(chunk)
        response = connection.getresponse()
        body = response.read().decode("utf-8", errors="replace").strip()
        if response.status >= 400:
            detail = f": {body}" if body else ""
            raise ObjectStorageUploadHTTPError(
                f"Object Storage upload failed with HTTP {response.status} {response.reason}{detail}"
            )
        return str(response.status), response.getheader("ETag", "")
    finally:
        connection.close()


def upload_with_curl(
    url: str,
    file_path: Path,
    *,
    headers: dict[str, str],
    timeout: float,
) -> str | None:
    curl = shutil.which("curl")
    if not curl:
        return None
    cmd = [
        curl,
        "--fail",
        "--silent",
        "--show-error",
        "--location",
        "--request",
        "PUT",
        "--max-time",
        str(int(timeout)),
        "--upload-file",
        str(file_path),
    ]
    for name, value in headers.items():
        cmd.extend(["--header", f"{name}: {value}"])
    cmd.append(url)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 0:
        return "200"
    return None


def presign_put_url(config: StorageConfig, object_key: str, *, expires_in: int = 3600) -> str:
    return presign_url(config, object_key, method="PUT", expires_in=expires_in)


def presign_get_url(config: StorageConfig, object_key: str, *, expires_in: int = 3600) -> str:
    return presign_url(config, object_key, method="GET", expires_in=expires_in)


def presign_url(config: StorageConfig, object_key: str, *, method: str, expires_in: int = 3600) -> str:
    if expires_in <= 0:
        raise SystemExit("--expires-in must be greater than zero")
    if expires_in > MAX_PRESIGN_TTL:
        raise SystemExit(f"--expires-in must be <= {MAX_PRESIGN_TTL}")

    timestamp = now_utc()
    amz_date = timestamp.strftime("%Y%m%dT%H%M%SZ")
    datestamp = timestamp.strftime("%Y%m%d")
    credential_scope = f"{datestamp}/{config.region}/{SERVICE}/aws4_request"

    parsed_endpoint = urllib.parse.urlparse(config.endpoint)
    host = bucket_host(config)
    canonical_uri = f"/{quote_object_key(object_key)}"

    query = {
        "X-Amz-Algorithm": ALGORITHM,
        "X-Amz-Credential": f"{config.access_key}/{credential_scope}",
        "X-Amz-Date": amz_date,
        "X-Amz-Expires": str(expires_in),
        "X-Amz-SignedHeaders": "host",
    }
    canonical_querystring = urllib.parse.urlencode(sorted(query.items()), quote_via=urllib.parse.quote, safe="-_.~")
    canonical_headers = f"host:{host}\n"
    canonical_request = build_canonical_request(
        method,
        canonical_uri,
        canonical_querystring,
        canonical_headers,
        "host",
        "UNSIGNED-PAYLOAD",
    )
    string_to_sign = build_string_to_sign(amz_date, credential_scope, canonical_request)
    signing_key = get_signing_key(config.secret_key, datestamp, config.region, SERVICE)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    signed_query = dict(query)
    signed_query["X-Amz-Signature"] = signature
    query_string = urllib.parse.urlencode(sorted(signed_query.items()), quote_via=urllib.parse.quote, safe="-_.~")
    return f"{parsed_endpoint.scheme}://{host}{canonical_uri}?{query_string}"
