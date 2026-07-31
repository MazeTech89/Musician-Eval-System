"""Lightweight audio similarity analysis helpers for performance scoring."""

from __future__ import annotations

import math
import struct
import wave
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AudioFeatures:
    """Simple audio characteristics used for similarity scoring."""

    duration_seconds: float
    rms_energy: float
    peak_amplitude: float
    zero_crossing_rate: float
    frequency_estimate: float
    histogram: tuple[float, ...]
    delta_profile: tuple[float, ...]


@dataclass(frozen=True)
class SimilarityAnalysis:
    """Similarity score and the breakdown used to produce the score."""

    score: float
    duration_similarity: float
    energy_similarity: float
    peak_similarity: float
    zero_crossing_similarity: float
    histogram_similarity: float
    delta_profile_similarity: float


def _extract_samples(audio_path: Path) -> list[float]:
    """Extract PCM samples from a WAV file."""
    with wave.open(str(audio_path), "rb") as wav_file:
        if wav_file.getnframes() == 0:
            raise ValueError("Audio file is empty")

        sample_width = wav_file.getsampwidth()
        channel_count = wav_file.getnchannels()
        raw_frames = wav_file.readframes(wav_file.getnframes())

        if sample_width == 2:
            fmt = f"<{channel_count}h"
            unpacked_frames = struct.iter_unpack(fmt, raw_frames)
            return [sum(frame_values) / channel_count for frame_values in unpacked_frames]

        if sample_width == 1:
            fmt = f"<{channel_count}B"
            unpacked_frames = struct.iter_unpack(fmt, raw_frames)
            return [
                sum((value - 128) for value in frame_values) / channel_count
                for frame_values in unpacked_frames
            ]

        raise ValueError("Only 8-bit or 16-bit PCM WAV files are supported")


def _build_histogram(samples: list[float], bins: int = 16) -> tuple[float, ...]:
    """Create a normalized amplitude histogram for a sample series."""
    if not samples:
        return tuple([0.0] * bins)

    peak_amplitude = max(abs(sample) for sample in samples)
    if peak_amplitude == 0:
        return tuple([0.0] * bins)

    histogram = [0.0] * bins
    for sample in samples:
        normalized = max(-1.0, min(1.0, sample / peak_amplitude))
        bucket = int((normalized + 1.0) * ((bins / 2) - 0.5))
        bucket = max(0, min(bins - 1, bucket))
        histogram[bucket] += 1.0

    total = sum(histogram)
    if total == 0:
        return tuple([0.0] * bins)

    return tuple(value / total for value in histogram)


def _calculate_zero_crossing_rate(samples: list[float]) -> float:
    """Estimate the zero-crossing rate for the sample series."""
    if len(samples) < 2:
        return 0.0

    crossings = 0
    for previous, current in zip(samples, samples[1:], strict=False):
        if previous == 0.0 or current == 0.0:
            continue
        if previous < 0.0 < current or current < 0.0 < previous:
            crossings += 1

    return crossings / max(1, len(samples) - 1)


def _build_delta_profile(samples: list[float], segments: int = 8) -> tuple[float, ...]:
    """Create a normalized profile of waveform changes across the sample stream."""
    if not samples:
        return tuple([0.0] * segments)

    segment_size = max(1, len(samples) // segments)
    profile: list[float] = []
    for segment_index in range(segments):
        start = segment_index * segment_size
        end = min(len(samples), start + segment_size)
        if end - start < 2:
            profile.append(0.0)
            continue

        delta_total = sum(
            abs(samples[index] - samples[index - 1]) for index in range(start + 1, end)
        )
        profile.append(delta_total / max(1, end - start - 1))

    max_value = max(profile, default=0.0)
    if max_value == 0.0:
        return tuple([0.0] * segments)

    return tuple(value / max_value for value in profile)


def build_audio_features(audio_path: str | Path) -> AudioFeatures:
    """Extract a feature profile from a WAV audio file."""
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(path)

    with wave.open(str(path), "rb") as wav_file:
        frame_rate = wav_file.getframerate()
        frame_count = wav_file.getnframes()
        samples = _extract_samples(path)

    duration_seconds = frame_count / frame_rate if frame_rate else 0.0
    if not samples:
        raise ValueError("Audio file did not contain any samples")

    rms_energy = math.sqrt(sum(sample * sample for sample in samples) / len(samples))
    peak_amplitude = max(abs(sample) for sample in samples)
    zero_crossing_rate = _calculate_zero_crossing_rate(samples)
    frequency_estimate = (zero_crossing_rate * frame_rate) / 2.0 if frame_rate else 0.0
    histogram = _build_histogram(samples)
    delta_profile = _build_delta_profile(samples)

    return AudioFeatures(
        duration_seconds=duration_seconds,
        rms_energy=rms_energy,
        peak_amplitude=peak_amplitude,
        zero_crossing_rate=zero_crossing_rate,
        frequency_estimate=frequency_estimate,
        histogram=histogram,
        delta_profile=delta_profile,
    )


def _similarity_component(reference_value: float, candidate_value: float) -> float:
    """Return a 0-1 similarity component based on the absolute difference."""
    if reference_value == 0.0 and candidate_value == 0.0:
        return 1.0

    denominator = max(abs(reference_value), abs(candidate_value), 1e-9)
    return max(0.0, 1.0 - (abs(reference_value - candidate_value) / denominator))


def _cosine_similarity(
    reference_values: tuple[float, ...],
    candidate_values: tuple[float, ...],
) -> float:
    """Compare two numeric profiles using cosine similarity."""
    if not reference_values or not candidate_values:
        return 0.0

    numerator = sum(a * b for a, b in zip(reference_values, candidate_values, strict=False))
    reference_norm = math.sqrt(sum(value * value for value in reference_values))
    candidate_norm = math.sqrt(sum(value * value for value in candidate_values))

    if reference_norm == 0.0 or candidate_norm == 0.0:
        return 0.0

    return numerator / (reference_norm * candidate_norm)


def score_audio_similarity(
    reference_audio_path: str | Path,
    candidate_audio_path: str | Path,
) -> SimilarityAnalysis:
    """Score how similar two WAV files are using lightweight acoustic features."""
    reference_features = build_audio_features(reference_audio_path)
    candidate_features = build_audio_features(candidate_audio_path)

    duration_similarity = _similarity_component(
        reference_features.duration_seconds,
        candidate_features.duration_seconds,
    )
    energy_similarity = _similarity_component(
        reference_features.rms_energy,
        candidate_features.rms_energy,
    )
    peak_similarity = _similarity_component(
        reference_features.peak_amplitude,
        candidate_features.peak_amplitude,
    )
    zero_crossing_similarity = _similarity_component(
        reference_features.zero_crossing_rate,
        candidate_features.zero_crossing_rate,
    )
    frequency_similarity = _similarity_component(
        reference_features.frequency_estimate,
        candidate_features.frequency_estimate,
    )
    histogram_similarity = _cosine_similarity(
        reference_features.histogram,
        candidate_features.histogram,
    )
    delta_profile_similarity = _cosine_similarity(
        reference_features.delta_profile,
        candidate_features.delta_profile,
    )

    score = (
        (duration_similarity * 0.1)
        + (energy_similarity * 0.15)
        + (peak_similarity * 0.1)
        + (zero_crossing_similarity * 0.1)
        + (frequency_similarity * 0.25)
        + (histogram_similarity * 0.1)
        + (delta_profile_similarity * 0.2)
    ) * 100.0

    return SimilarityAnalysis(
        score=round(max(0.0, min(100.0, score)), 2),
        duration_similarity=round(duration_similarity, 4),
        energy_similarity=round(energy_similarity, 4),
        peak_similarity=round(peak_similarity, 4),
        zero_crossing_similarity=round(zero_crossing_similarity, 4),
        histogram_similarity=round(histogram_similarity, 4),
        delta_profile_similarity=round(delta_profile_similarity, 4),
    )
