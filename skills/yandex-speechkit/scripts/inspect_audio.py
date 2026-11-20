#!/usr/bin/env python3
"""Inspect an audio file and suggest a SpeechKit-friendly path."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path


def run_ffprobe(path: Path) -> dict | None:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None

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
        raise RuntimeError(proc.stderr.strip() or "ffprobe failed")
    return json.loads(proc.stdout)


def inspect_wav(path: Path) -> dict:
    with wave.open(str(path), "rb") as wav_file:
        frames = wav_file.getnframes()
        sample_rate = wav_file.getframerate()
        duration = frames / sample_rate if sample_rate else 0
        sample_width = wav_file.getsampwidth()
        channels = wav_file.getnchannels()
    return {
        "container": "wav",
        "codec": "pcm_s16le" if sample_width == 2 else f"pcm_{sample_width * 8}bit",
        "sample_rate_hz": sample_rate,
        "channels": channels,
        "duration_seconds": round(duration, 3),
    }


def guess_mode(duration: float | None, channels: int | None) -> str:
    if duration is None:
        return "unknown"
    if duration <= 30 and (channels or 1) == 1:
        return "synchronous-or-streaming-if-live"
    if duration <= 300 and (channels or 1) == 1:
        return "streaming-if-live-otherwise-consider-async"
    return "asynchronous"


def suggest_conversion(codec: str | None, container: str | None, channels: int | None) -> str | None:
    supported = {
        ("wav", "pcm_s16le"),
        ("ogg", "opus"),
        ("ogg", "libopus"),
        ("mp3", "mp3"),
    }
    normalized_codec = (codec or "").lower()
    normalized_container = (container or "").lower()

    if (normalized_container, normalized_codec) in supported and (channels or 1) in {1, 2}:
        return None
    return "convert-to-wav-mono-16000hz-or-ogg-opus-before-sending"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio_file", help="Path to a local audio file")
    args = parser.parse_args()

    path = Path(args.audio_file).expanduser().resolve()
    if not path.is_file():
        print(json.dumps({"error": f"File not found: {path}"}))
        return 1

    result: dict[str, object] = {
        "path": str(path),
        "size_bytes": path.stat().st_size,
    }

    try:
        probe = run_ffprobe(path)
        if probe and probe.get("streams"):
            audio_stream = next((s for s in probe["streams"] if s.get("codec_type") == "audio"), None)
            fmt = probe.get("format", {})
            result.update(
                {
                    "container": fmt.get("format_name"),
                    "codec": audio_stream.get("codec_name") if audio_stream else None,
                    "sample_rate_hz": int(audio_stream["sample_rate"]) if audio_stream and audio_stream.get("sample_rate") else None,
                    "channels": audio_stream.get("channels") if audio_stream else None,
                    "duration_seconds": float(fmt["duration"]) if fmt.get("duration") else None,
                }
            )
        elif path.suffix.lower() == ".wav":
            result.update(inspect_wav(path))
        else:
            result["note"] = "No ffprobe available; limited inspection only."
    except Exception as exc:  # pragma: no cover - defensive CLI behavior
        if path.suffix.lower() == ".wav":
            result.update(inspect_wav(path))
            result["note"] = f"ffprobe inspection failed, used wave fallback: {exc}"
        else:
            result["error"] = str(exc)
            print(json.dumps(result, indent=2))
            return 1

    duration = result.get("duration_seconds")
    channels = result.get("channels")
    codec = result.get("codec")
    container = result.get("container")

    result["speechkit_recommendation"] = {
        "mode": guess_mode(duration if isinstance(duration, (int, float)) else None, channels if isinstance(channels, int) else None),
        "conversion": suggest_conversion(codec if isinstance(codec, str) else None, container if isinstance(container, str) else None, channels if isinstance(channels, int) else None),
    }

    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
