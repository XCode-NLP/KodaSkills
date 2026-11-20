#!/usr/bin/env python3
"""Split a local audio file by size and transcribe each chunk with sync SpeechKit."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from env_config import has_object_storage_env, load_project_env


load_project_env()


DEFAULT_SYNC_SAMPLE_RATE = 16000


def progress(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def run_json(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip() or f"Command failed: {' '.join(cmd)}"
        raise SystemExit(message)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive CLI behavior
        raise SystemExit(f"Expected JSON output from command: {' '.join(cmd)}") from exc


def detect_sync_format(path: Path, explicit_format: str | None) -> str | None:
    if explicit_format and explicit_format != "lpcm":
        raise SystemExit("transcribe_local_in_parts.py converts chunks to raw LINEAR16; use --format lpcm or omit --format.")
    return "lpcm"


def write_manifest(path: Path, manifest: dict[str, object]) -> None:
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True), encoding="utf-8")


def convert_chunk_to_linear16(base_dir: Path, source: Path, target: Path, sample_rate: int) -> None:
    if target.exists():
        return
    cmd = [
        sys.executable,
        str(base_dir / "prepare_audio.py"),
        str(source),
        str(target),
        "--format",
        "linear16",
        "--sample-rate",
        str(sample_rate),
        "--channels",
        "1",
        "--overwrite",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip() or f"Command failed: {' '.join(cmd)}"
        raise SystemExit(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", help="Source audio file to split and transcribe")
    parser.add_argument("work_dir", help="Directory where chunks and results will be written")
    parser.add_argument("--max-bytes", type=int, help="Maximum size of each chunk in bytes")
    parser.add_argument("--max-size-mb", type=float, help="Maximum size of each chunk in MiB")
    parser.add_argument("--margin", type=float, default=0.97, help="Safety multiplier for chunk size")
    parser.add_argument("--min-segment-seconds", type=float, default=1.0, help="Minimum recursive split size")
    parser.add_argument("--lang", default="ru-RU", help="Recognition language")
    parser.add_argument("--topic", default="general", help="Recognition model/topic")
    parser.add_argument("--folder-id", help="Folder ID when required by your auth flow")
    parser.add_argument("--format", dest="audio_format", help="SpeechKit sync format parameter, e.g. lpcm")
    parser.add_argument(
        "--sample-rate-hertz",
        type=int,
        default=DEFAULT_SYNC_SAMPLE_RATE,
        help="Sample rate query parameter for raw LINEAR16 chunks",
    )
    parser.add_argument("--profanity-filter", action="store_true", help="Enable profanity filter")
    parser.add_argument("--api-key", help="Yandex API key")
    parser.add_argument("--iam-token", help="Yandex IAM token")
    parser.add_argument("--prefix", default=None, help="Optional prefix for generated chunk names")
    parser.add_argument("--dry-run", action="store_true", help="Only split and prepare manifest without API calls")
    parser.add_argument("--resume", action="store_true", help="Skip chunks that already have result files")
    parser.add_argument("--retries", type=int, default=3, help="Attempts per chunk for transient sync failures")
    parser.add_argument("--retry-backoff", type=float, default=2.0, help="Initial retry backoff in seconds")
    args = parser.parse_args()

    if has_object_storage_env():
        raise SystemExit(
            "Object Storage settings are present in .env or process env. "
            "This project must use async transcription in that case. "
            "Run scripts/transcribe_file_async.py instead of transcribe_local_in_parts.py."
        )

    base_dir = Path(__file__).resolve().parent
    input_path = Path(args.input_file).expanduser().resolve()
    if not input_path.is_file():
        raise SystemExit(f"Input file not found: {input_path}")

    work_dir = Path(args.work_dir).expanduser().resolve()
    chunks_dir = work_dir / "chunks"
    raw_chunks_dir = work_dir / "raw_chunks"
    results_dir = work_dir / "results"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    raw_chunks_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    split_cmd = [
        sys.executable,
        str(base_dir / "split_audio_by_size.py"),
        str(input_path),
        str(chunks_dir),
        "--margin",
        str(args.margin),
        "--min-segment-seconds",
        str(args.min_segment_seconds),
    ]
    if args.max_bytes is not None:
        split_cmd.extend(["--max-bytes", str(args.max_bytes)])
    if args.max_size_mb is not None:
        split_cmd.extend(["--max-size-mb", str(args.max_size_mb)])
    if args.prefix:
        split_cmd.extend(["--prefix", args.prefix])

    split_manifest = run_json(split_cmd)
    parts = split_manifest.get("parts") or []
    if not isinstance(parts, list) or not parts:
        raise SystemExit("Split step did not produce any chunks")

    final_parts: list[dict[str, object]] = []
    transcript_blocks: list[str] = []
    manifest_path = work_dir / "manifest.json"
    transcript_path = work_dir / "transcript.txt"

    for index, part in enumerate(parts, start=1):
        if not isinstance(part, dict) or "path" not in part:
            raise SystemExit("Split manifest contains an invalid part entry")
        part_path = Path(str(part["path"]))
        raw_part_path = raw_chunks_dir / f"part{index:03d}.s16le"
        transcript_path = results_dir / f"part{index:03d}.txt"

        entry: dict[str, object] = {
            "index": index,
            "path": str(part_path),
            "raw_linear16_path": str(raw_part_path),
            "start_seconds": part.get("start_seconds"),
            "duration_seconds": part.get("duration_seconds"),
            "size_bytes": part.get("size_bytes"),
            "transcript_path": str(transcript_path),
        }

        if args.resume and transcript_path.is_file():
            transcript = transcript_path.read_text(encoding="utf-8").strip()
            entry["status"] = "ok"
            entry["text"] = transcript
            entry["resumed"] = True
            final_parts.append(entry)
            transcript_blocks.append(transcript)
            progress(f"part {index}/{len(parts)}: resumed")
            continue

        if args.dry_run:
            entry["status"] = "dry-run"
            final_parts.append(entry)
            continue

        convert_chunk_to_linear16(base_dir, part_path, raw_part_path, args.sample_rate_hertz)
        progress(f"part {index}/{len(parts)} prepared: {raw_part_path}")

        recognize_cmd = [
            sys.executable,
            str(base_dir / "speechkit_sync_recognize.py"),
            str(raw_part_path),
            "--lang",
            args.lang,
            "--topic",
            args.topic,
        ]
        if args.folder_id:
            recognize_cmd.extend(["--folder-id", args.folder_id])

        detected_format = detect_sync_format(part_path, args.audio_format)
        if detected_format:
            recognize_cmd.extend(["--format", detected_format])
        recognize_cmd.extend(["--sample-rate-hertz", str(args.sample_rate_hertz)])
        if args.profanity_filter:
            recognize_cmd.append("--profanity-filter")
        if args.api_key:
            recognize_cmd.extend(["--api-key", args.api_key])
        if args.iam_token:
            recognize_cmd.extend(["--iam-token", args.iam_token])

        proc = None
        for attempt in range(1, max(args.retries, 1) + 1):
            proc = subprocess.run(recognize_cmd, capture_output=True, text=True)
            if proc.returncode == 0:
                break
            error_text = proc.stderr.strip() or proc.stdout.strip() or "Unknown recognition error"
            transient = any(
                marker in error_text.lower()
                for marker in ("broken pipe", "urlerror", "timed out", "timeout", "connection reset")
            )
            if not transient or attempt >= max(args.retries, 1):
                break
            progress(f"part {index}/{len(parts)} retry {attempt + 1}: {error_text}")
            time.sleep(args.retry_backoff * (2 ** (attempt - 1)))

        if proc is None or proc.returncode != 0:
            entry["status"] = "error"
            entry["error"] = (
                "recognition process did not start"
                if proc is None
                else proc.stderr.strip() or proc.stdout.strip() or "Unknown recognition error"
            )
            final_parts.append(entry)
            partial_manifest = {
                "source": str(input_path),
                "status": "error",
                "chunking": split_manifest,
                "parts": final_parts,
                "transcript_path": str(work_dir / "transcript.txt"),
            }
            write_manifest(manifest_path, partial_manifest)
            break

        transcript = proc.stdout.strip()
        transcript_path.write_text(transcript + ("\n" if transcript else ""), encoding="utf-8")
        entry["status"] = "ok"
        entry["text"] = transcript
        final_parts.append(entry)
        transcript_blocks.append(transcript)
        progress(f"part {index}/{len(parts)} saved: {transcript_path}")
        partial_manifest = {
            "source": str(input_path),
            "status": "running",
            "chunking": split_manifest,
            "parts": final_parts,
            "transcript_path": str(work_dir / "transcript.txt"),
        }
        write_manifest(manifest_path, partial_manifest)

    overall_status = "ok"
    if any(part.get("status") == "error" for part in final_parts):
        overall_status = "error"
    elif args.dry_run:
        overall_status = "dry-run"

    transcript_path = work_dir / "transcript.txt"
    if transcript_blocks:
        transcript_path.write_text("\n\n".join(block for block in transcript_blocks if block), encoding="utf-8")
        progress(f"saved transcript: {transcript_path}")

    manifest = {
        "source": str(input_path),
        "status": overall_status,
        "chunking": split_manifest,
        "parts": final_parts,
        "transcript_path": str(transcript_path),
    }
    write_manifest(manifest_path, manifest)
    print(json.dumps(manifest, indent=2, ensure_ascii=True))
    return 0 if overall_status != "error" else 1


if __name__ == "__main__":
    sys.exit(main())
