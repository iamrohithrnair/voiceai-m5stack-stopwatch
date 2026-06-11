from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


class FfmpegError(RuntimeError):
    pass


def _require_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise FfmpegError(
            "ffmpeg not found. Install it (e.g. brew install ffmpeg) for audio conversion."
        )
    return path


def opus_packets_to_wav(packets: list[bytes], sample_rate: int = 16000) -> bytes:
    """Decode a list of raw Opus frames to WAV bytes."""
    _require_ffmpeg()
    if not packets:
        raise ValueError("No audio packets to decode")

    with tempfile.TemporaryDirectory() as tmp:
        opus_path = Path(tmp) / "input.opus"
        wav_path = Path(tmp) / "output.wav"
        opus_path.write_bytes(b"".join(packets))

        proc = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(opus_path),
                "-ar",
                str(sample_rate),
                "-ac",
                "1",
                str(wav_path),
            ],
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0 or not wav_path.exists():
            raise FfmpegError(proc.stderr.decode("utf-8", errors="replace"))

        return wav_path.read_bytes()


def mp3_to_opus_packets(mp3_data: bytes, sample_rate: int = 24000, frame_ms: int = 60) -> list[bytes]:
    """Encode MP3 audio into Opus frames for the device speaker."""
    _require_ffmpeg()
    with tempfile.TemporaryDirectory() as tmp:
        mp3_path = Path(tmp) / "input.mp3"
        opus_path = Path(tmp) / "output.opus"
        mp3_path.write_bytes(mp3_data)

        proc = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(mp3_path),
                "-ar",
                str(sample_rate),
                "-ac",
                "1",
                "-c:a",
                "libopus",
                "-frame_duration",
                str(frame_ms),
                "-f",
                "opus",
                str(opus_path),
            ],
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0 or not opus_path.exists():
            raise FfmpegError(proc.stderr.decode("utf-8", errors="replace"))

        # Split Ogg/Opus container into individual packets for WebSocket binary frames.
        return _split_ogg_opus_packets(opus_path.read_bytes())


def _split_ogg_opus_packets(ogg_data: bytes) -> list[bytes]:
    """Extract Opus packets from an Ogg container."""
    packets: list[bytes] = []
    offset = 0
    while offset + 27 <= len(ogg_data):
        if ogg_data[offset : offset + 4] != b"OggS":
            break
        num_segments = ogg_data[offset + 26]
        seg_start = offset + 27
        seg_end = seg_start + num_segments
        if seg_end > len(ogg_data):
            break
        body = seg_end
        for size in ogg_data[seg_start:seg_end]:
            segment = ogg_data[body : body + size]
            body += size
            if segment.startswith(b"OpusHead") or segment.startswith(b"OpusTags"):
                continue
            if segment:
                packets.append(segment)
        offset = body
    return packets
