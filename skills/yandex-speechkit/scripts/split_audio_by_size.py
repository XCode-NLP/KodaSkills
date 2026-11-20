#!/usr/bin/env python3
"""Split an audio file into chunks that stay below a maximum file size."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_MARGIN = 0.97


def run_ffprobe(path: Path) -> dict:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise SystemExit("ffprobe not found in PATH")

    cmd = [
        ffprobe,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or "ffprobe failed")
    return json.loads(proc.stdout)


def has_non_audio_streams(probe: dict) -> bool:
    streams = probe.get("streams") or []
    return any(stream.get("codec_type") != "audio" for stream in streams)


def detect_extension(path: Path, probe: dict) -> str:
    suffix = path.suffix.lstrip(".").lower()
    if suffix:
        return suffix
    format_name = str((probe.get("format") or {}).get("format_name") or "")
    primary = format_name.split(",")[0].strip().lower()
    return primary or "audio"


def copy_audio_segment(
    ffmpeg: str,
    input_path: Path,
    output_path: Path,
    start: float | None = None,
    duration: float | None = None,
) -> None:
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
    ]
    if start is not None:
        cmd.extend(["-ss", f"{start:.6f}"])
    if duration is not None:
        cmd.extend(["-t", f"{duration:.6f}"])
    cmd.extend(
        [
        "-i",
        str(input_path),
        "-map",
        "0:a:0",
        "-vn",
        "-sn",
        "-dn",
        "-c:a",
        "copy",
        str(output_path),
        ]
    )
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        segment_hint = f" for segment starting at {start}" if start is not None else ""
        raise RuntimeError(proc.stderr.strip() or f"ffmpeg failed{segment_hint}")


def max_bytes_from_args(args: argparse.Namespace) -> int:
    if args.max_bytes is not None:
        if args.max_bytes <= 0:
            raise SystemExit("--max-bytes must be greater than zero")
        return args.max_bytes
    if args.max_size_mb is None or args.max_size_mb <= 0:
        raise SystemExit("Provide --max-bytes or --max-size-mb with a value greater than zero")
    return int(args.max_size_mb * 1024 * 1024)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", help="Source audio file to split")
    parser.add_argument("output_dir", help="Directory where chunks will be written")
    parser.add_argument("--max-bytes", type=int, help="Maximum size of each chunk in bytes")
    parser.add_argument("--max-size-mb", type=float, help="Maximum size of each chunk in MiB")
    parser.add_argument(
        "--margin",
        type=float,
        default=DEFAULT_MARGIN,
        help="Safety multiplier below the requested limit, default: %(default)s",
    )
    parser.add_argument(
        "--min-segment-seconds",
        type=float,
        default=1.0,
        help="Do not keep splitting below this duration, default: %(default)s",
    )
    parser.add_argument(
        "--prefix",
        default=None,
        help="Optional filename prefix for chunks, default: source filename stem",
    )
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg not found in PATH")

    input_path = Path(args.input_file).expanduser().resolve()
    if not input_path.is_file():
        raise SystemExit(f"Input file not found: {input_path}")

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    max_bytes = max_bytes_from_args(args)
    if not (0 < args.margin < 1):
        raise SystemExit("--margin must be between 0 and 1")
    if args.min_segment_seconds <= 0:
        raise SystemExit("--min-segment-seconds must be greater than zero")

    probe = run_ffprobe(input_path)
    duration = float((probe.get("format") or {}).get("duration") or 0.0)
    if duration <= 0:
        raise SystemExit("Could not determine audio duration")

    total_size = input_path.stat().st_size
    prefix = args.prefix or input_path.stem
    extension = detect_extension(input_path, probe)
    drop_non_audio_streams = has_non_audio_streams(probe)

    if total_size <= max_bytes:
        output_path = output_dir / f"{prefix}_part001.{extension}"
        if output_path != input_path:
            if drop_non_audio_streams:
                copy_audio_segment(ffmpeg, input_path, output_path)
            else:
                output_path.write_bytes(input_path.read_bytes())
        manifest = {
            "source": str(input_path),
            "max_bytes": max_bytes,
            "total_size_bytes": total_size,
            "duration_seconds": duration,
            "copied_without_split": True,
            "dropped_non_audio_streams": drop_non_audio_streams,
            "parts": [
                {
                    "path": str(output_path),
                    "start_seconds": 0.0,
                    "duration_seconds": duration,
                    "size_bytes": output_path.stat().st_size,
                }
            ],
        }
        print(json.dumps(manifest, indent=2, ensure_ascii=True))
        return 0

    effective_limit = max(1, int(max_bytes * args.margin))
    extension = extension or "audio"
    parts: list[dict[str, float | int | str]] = []

    def split_range(start: float, segment_duration: float) -> None:
        part_number = len(parts) + 1
        output_path = output_dir / f"{prefix}_part{part_number:03d}.{extension}"
        copy_audio_segment(ffmpeg, input_path, output_path, start, segment_duration)
        part_size = output_path.stat().st_size

        if part_size <= max_bytes or segment_duration <= args.min_segment_seconds:
            parts.append(
                {
                    "path": str(output_path),
                    "start_seconds": round(start, 3),
                    "duration_seconds": round(segment_duration, 3),
                    "size_bytes": part_size,
                }
            )
            return

        output_path.unlink()
        first_duration = max(args.min_segment_seconds, segment_duration / 2)
        second_duration = segment_duration - first_duration
        if second_duration <= 0:
            raise SystemExit(
                f"Could not produce a chunk under {max_bytes} bytes. "
                f"Try re-encoding to a lower bitrate before splitting."
            )
        split_range(start, first_duration)
        split_range(start + first_duration, second_duration)

    estimated_parts = max(1, math.ceil(total_size / effective_limit))
    target_duration = duration / estimated_parts
    current_start = 0.0

    while current_start < duration:
        remaining = duration - current_start
        current_duration = min(target_duration, remaining)
        split_range(current_start, current_duration)
        current_start += current_duration

    manifest = {
        "source": str(input_path),
        "max_bytes": max_bytes,
        "margin": args.margin,
        "total_size_bytes": total_size,
        "duration_seconds": duration,
        "dropped_non_audio_streams": drop_non_audio_streams,
        "parts": parts,
    }
    print(json.dumps(manifest, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
