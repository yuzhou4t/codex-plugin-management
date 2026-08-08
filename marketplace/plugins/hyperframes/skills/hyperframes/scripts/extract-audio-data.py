#!/usr/bin/env python3
"""Extract deterministic per-frame audio data for HyperFrames compositions."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

try:
    import numpy as np
except ModuleNotFoundError:
    np = None


SAMPLE_RATE = 44100
FFT_SIZE = 4096
MIN_FREQ = 30.0
MAX_FREQ = 16000.0


def decode_audio(path: str) -> np.ndarray:
    """Decode audio to mono float32 samples through ffmpeg."""
    command = [
        "ffmpeg",
        "-i",
        path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(SAMPLE_RATE),
        "-f",
        "s16le",
        "-acodec",
        "pcm_s16le",
        "-loglevel",
        "error",
        "pipe:1",
    ]
    result = subprocess.run(command, capture_output=True)
    if result.returncode != 0:
        print(f"ffmpeg error: {result.stderr.decode()}", file=sys.stderr)
        sys.exit(1)
    return np.frombuffer(result.stdout, dtype=np.int16).astype(np.float32) / 32768.0


def compute_band_edges(number_of_bands: int) -> np.ndarray:
    """Return logarithmically spaced frequency-band edges."""
    return np.array(
        [
            MIN_FREQ * (MAX_FREQ / MIN_FREQ) ** (index / number_of_bands)
            for index in range(number_of_bands + 1)
        ]
    )


def compute_fft_bands(
    windowed: np.ndarray,
    frequency_per_bin: float,
    number_of_bins: int,
    band_edges: np.ndarray,
    number_of_bands: int,
) -> np.ndarray:
    """Compute peak magnitude for each frequency band."""
    magnitudes = np.abs(np.fft.rfft(windowed))
    bands = np.zeros(number_of_bands)

    for band in range(number_of_bands):
        low_bin = max(0, int(band_edges[band] / frequency_per_bin))
        high_bin = min(number_of_bins, int(band_edges[band + 1] / frequency_per_bin))
        if high_bin <= low_bin:
            high_bin = low_bin + 1
        low_bin = min(low_bin, number_of_bins - 1)
        high_bin = min(high_bin, number_of_bins)
        bands[band] = np.max(magnitudes[low_bin:high_bin])

    return bands


def extract(path: str, fps: int, number_of_bands: int) -> dict:
    """Extract normalized RMS and frequency-band values for each frame."""
    print(f"Decoding audio from {path}...", file=sys.stderr)
    samples = decode_audio(path)
    duration = len(samples) / SAMPLE_RATE
    frame_step = SAMPLE_RATE // fps
    total_frames = int(duration * fps)

    print(
        f"Duration: {duration:.1f}s, {total_frames} frames at {fps}fps",
        file=sys.stderr,
    )

    hann = np.hanning(FFT_SIZE)
    band_edges = compute_band_edges(number_of_bands)
    frequency_per_bin = SAMPLE_RATE / FFT_SIZE
    number_of_bins = FFT_SIZE // 2 + 1
    half_fft = FFT_SIZE // 2

    rms_values = np.zeros(total_frames)
    band_values = np.zeros((total_frames, number_of_bands))

    for frame in range(total_frames):
        rms_start = frame * frame_step
        rms_end = rms_start + frame_step
        frame_slice = samples[rms_start : min(rms_end, len(samples))]
        if len(frame_slice) > 0:
            rms_values[frame] = np.sqrt(np.mean(frame_slice**2))

        center = rms_start + frame_step // 2
        window_start = center - half_fft
        window_end = center + half_fft

        if window_start >= 0 and window_end <= len(samples):
            window = samples[window_start:window_end] * hann
        else:
            padded = np.zeros(FFT_SIZE)
            source_start = max(0, window_start)
            source_end = min(len(samples), window_end)
            destination_start = source_start - window_start
            destination_end = destination_start + (source_end - source_start)
            padded[destination_start:destination_end] = samples[source_start:source_end]
            window = padded * hann

        band_values[frame] = compute_fft_bands(
            window,
            frequency_per_bin,
            number_of_bins,
            band_edges,
            number_of_bands,
        )

    peak_rms = rms_values.max() if total_frames > 0 else 1.0
    if peak_rms > 0:
        rms_values /= peak_rms

    band_peaks = band_values.max(axis=0)
    band_peaks[band_peaks == 0] = 1.0
    band_values /= band_peaks

    frames = [
        {
            "time": round(frame / fps, 4),
            "rms": round(float(rms_values[frame]), 4),
            "bands": [round(float(value), 4) for value in band_values[frame]],
        }
        for frame in range(total_frames)
    ]

    return {
        "duration": round(duration, 4),
        "fps": fps,
        "bands": number_of_bands,
        "totalFrames": total_frames,
        "frames": frames,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract per-frame audio visualization data"
    )
    parser.add_argument("input", help="Audio or video file")
    parser.add_argument(
        "-o", "--output", default="audio-data.json", help="Output JSON path"
    )
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument(
        "--bands", type=int, default=16, help="Number of frequency bands"
    )
    args = parser.parse_args()

    if np is None:
        parser.error("numpy is required; install it in the Python environment used here")
    if args.fps < 1:
        parser.error("--fps must be at least 1")
    if args.bands < 1:
        parser.error("--bands must be at least 1")

    data = extract(args.input, args.fps, args.bands)

    with open(args.output, "w", encoding="utf-8") as output_file:
        json.dump(data, output_file)

    print(
        f"Wrote {args.output} ({data['totalFrames']} frames, "
        f"{data['bands']} bands)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
