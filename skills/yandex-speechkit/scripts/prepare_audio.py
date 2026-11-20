#!/usr/bin/env python3
"""Convert audio into SpeechKit-friendly formats using ffmpeg."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


FORMAT_PRESETS = {
    "wav": ["-c:a", "pcm_s16le", "-f", "wav"],
    "linear16": ["-c:a", "pcm_s16le", "-f", "s16le"],
    "ogg-opus": ["-c:a", "libopus", "-f", "ogg"],
    "mp3": ["-c:a", "libmp3lame", "-f", "mp3"],
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", help="Source audio or video file")
    parser.add_argument("output_file", help="Converted output file")
    parser.add_argument(
        "--format",
        choices=sorted(FORMAT_PRESETS),
        default="wav",
        help="Target audio format preset",
    )
    parser.add_argument("--sample-rate", type=int, default=16000, help="Target sample rate in Hz")
    parser.add_argument("--channels", type=int, default=1, help="Target channel count")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output")
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("ffmpeg not found in PATH", file=sys.stderr)
        return 1

    input_path = Path(args.input_file).expanduser().resolve()
    output_path = Path(args.output_file).expanduser().resolve()
    if not input_path.is_file():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1
    if output_path.exists() and not args.overwrite:
        print(f"Output file already exists: {output_path}. Use --overwrite to replace it.", file=sys.stderr)
        return 1

    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y" if args.overwrite else "-n",
        "-i",
        str(input_path),
        "-map",
        "0:a:0",
        "-vn",
        "-sn",
        "-dn",
        "-ac",
        str(args.channels),
        "-ar",
        str(args.sample_rate),
        *FORMAT_PRESETS[args.format],
        str(output_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 and proc.stderr:
        print(proc.stderr.strip(), file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
