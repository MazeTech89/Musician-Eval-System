"""Tests for lightweight audio similarity scoring."""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

from app.services.audio_similarity import score_audio_similarity


def _write_wav(path: Path, frequency: float, duration_seconds: float = 0.15) -> None:
    """Create a simple sine-wave WAV file at the given path."""
    sample_rate = 22050
    total_samples = int(sample_rate * duration_seconds)
    amplitude = 16000

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        for sample_index in range(total_samples):
            sample_value = int(
                amplitude * math.sin(2 * math.pi * frequency * sample_index / sample_rate)
            )
            wav_file.writeframes(struct.pack("<h", sample_value))


def test_similarity_score_rises_for_matching_audio(tmp_path: Path) -> None:
    """Matching audio should produce a high similarity score."""
    reference_path = tmp_path / "reference.wav"
    candidate_path = tmp_path / "candidate.wav"
    _write_wav(reference_path, 440.0)
    _write_wav(candidate_path, 440.0)

    analysis = score_audio_similarity(reference_path, candidate_path)

    assert analysis.score > 90.0


def test_similarity_score_is_lower_for_different_audio(tmp_path: Path) -> None:
    """Different tones should produce a lower similarity score."""
    reference_path = tmp_path / "reference.wav"
    candidate_path = tmp_path / "candidate.wav"
    _write_wav(reference_path, 440.0)
    _write_wav(candidate_path, 880.0)

    analysis = score_audio_similarity(reference_path, candidate_path)

    assert analysis.score < 90.0
