"""PyTorch + Librosa audio similarity analysis for performance scoring.

Features extracted per track:
- Pitch accuracy    : Mean fundamental frequency via YIN algorithm
- Tempo stability   : BPM + inter-beat interval regularity
- Rhythm consistency: Onset strength profile (cosine similarity via PyTorch)
- Dynamics          : Root-mean-square energy
- Timbre            : 13 MFCC coefficients (cosine similarity via PyTorch)

Scoring weights (sum to 1.0):
  pitch_accuracy     25 %
  tempo_stability    20 %
  rhythm_consistency 20 %
  dynamics_similarity 15 %
  timbre_similarity  20 %
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import librosa
import numpy as np
import torch
import torch.nn.functional as F

logger = logging.getLogger(__name__)

# Number of onset-strength frames kept for rhythm comparison
_ONSET_PROFILE_FRAMES = 100


@dataclass(frozen=True)
class AudioFeatures:
    """Musical feature vector extracted from an audio file."""

    duration_seconds: float
    pitch_mean_hz: float
    tempo_bpm: float
    beat_regularity: float
    onset_profile: tuple[float, ...]
    rms_energy: float
    mfcc_vector: tuple[float, ...]


@dataclass(frozen=True)
class SimilarityAnalysis:
    """Score and explainable breakdown of audio similarity.

    All component values are in [0, 1].  ``score`` is the weighted
    aggregate on a 0–100 scale.
    """

    score: float
    # Explainable components (FR-11)
    pitch_accuracy: float
    tempo_stability: float
    rhythm_consistency: float
    dynamics_similarity: float
    timbre_similarity: float
    # Legacy scalar fields kept for API backward compatibility
    duration_similarity: float
    energy_similarity: float
    # Metadata for transparency
    reference_tempo_bpm: float
    candidate_tempo_bpm: float
    reference_pitch_hz: float
    candidate_pitch_hz: float


def _scalar_similarity(a: float, b: float) -> float:
    """Return a 0–1 similarity for two scalar values."""
    # Treat dual-zero values as identical instead of dividing by near-zero magnitude.
    if a == 0.0 and b == 0.0:
        return 1.0
    denominator = max(abs(a), abs(b), 1e-9)
    return float(max(0.0, 1.0 - abs(a - b) / denominator))


def _cosine_sim_torch(u: tuple[float, ...], v: tuple[float, ...]) -> float:
    """Compute cosine similarity between two equal-length vectors via PyTorch."""
    if not u or not v:
        return 0.0
    # Convert to rank-2 tensors so cosine similarity runs on a stable batch dimension.
    t_u = torch.tensor(list(u), dtype=torch.float32).unsqueeze(0)
    t_v = torch.tensor(list(v), dtype=torch.float32).unsqueeze(0)
    result = F.cosine_similarity(t_u, t_v, dim=1).item()
    return float(max(0.0, result))


def _onset_profile(onset_env: np.ndarray) -> tuple[float, ...]:
    """Normalise an onset-strength array to a fixed-length profile."""
    n = _ONSET_PROFILE_FRAMES
    if len(onset_env) == 0:
        return tuple([0.0] * n)
    # Truncate or pad onset envelope so rhythm vectors remain comparable.
    if len(onset_env) >= n:
        profile = onset_env[:n].copy()
    else:
        profile = np.pad(onset_env, (0, n - len(onset_env)))
    max_val = float(np.max(profile))
    if max_val > 0:
        profile = profile / max_val
    return tuple(float(x) for x in profile)


def build_audio_features(audio_path: str | Path) -> AudioFeatures:
    """Extract musical features from an audio file using Librosa.

    Supports any format handled by soundfile / audioread (WAV, MP3,
    FLAC, OGG, …).
    """
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(path)

    # Keep original sample rate (sr=None) and mix to mono for consistent feature extraction.
    y, sr = librosa.load(str(path), sr=None, mono=True)
    if len(y) == 0:
        raise ValueError("Audio file contains no samples")

    duration = float(len(y)) / sr

    # --- Pitch (YIN) ---
    try:
        f0 = librosa.yin(y, fmin=50.0, fmax=2000.0, sr=sr)
        voiced = f0[f0 > 50.0]
        pitch_mean = float(np.mean(voiced)) if len(voiced) > 0 else 0.0
    except Exception:
        logger.warning("Pitch extraction failed for %s; defaulting to 0", path.name)
        pitch_mean = 0.0

    # --- Tempo + beat regularity ---
    try:
        tempo_result = librosa.beat.beat_track(y=y, sr=sr)
        tempo_bpm = float(tempo_result[0])
        beat_frames = tempo_result[1]
        if len(beat_frames) > 1:
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            ibi = np.diff(beat_times)
            mean_ibi = float(np.mean(ibi))
            regularity = 1.0 - float(np.std(ibi) / (mean_ibi + 1e-9))
            beat_regularity = float(np.clip(regularity, 0.0, 1.0))
        else:
            beat_regularity = 1.0
    except Exception:
        logger.warning("Tempo extraction failed for %s; defaulting", path.name)
        tempo_bpm = 120.0
        beat_regularity = 1.0

    # --- Onset strength (rhythm) ---
    try:
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_prof = _onset_profile(onset_env)
    except Exception:
        onset_prof = tuple([0.0] * _ONSET_PROFILE_FRAMES)

    # --- Dynamics (RMS energy) ---
    try:
        rms = librosa.feature.rms(y=y)[0]
        rms_energy = float(np.mean(rms))
    except Exception:
        rms_energy = 0.0

    # --- Timbre (MFCC, 13 coefficients) ---
    try:
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = tuple(float(x) for x in np.mean(mfcc, axis=1))
    except Exception:
        mfcc_mean = tuple([0.0] * 13)

    return AudioFeatures(
        duration_seconds=duration,
        pitch_mean_hz=pitch_mean,
        tempo_bpm=tempo_bpm,
        beat_regularity=beat_regularity,
        onset_profile=onset_prof,
        rms_energy=rms_energy,
        mfcc_vector=mfcc_mean,
    )


def score_audio_similarity(
    reference_audio_path: str | Path,
    candidate_audio_path: str | Path,
) -> SimilarityAnalysis:
    """Score how similar two audio files are using Librosa features and PyTorch.

    Returns a :class:`SimilarityAnalysis` with an overall score (0–100)
    and an explainable component breakdown (FR-08 through FR-11).
    """
    # Extract comparable feature vectors from both recordings.
    ref = build_audio_features(reference_audio_path)
    cand = build_audio_features(candidate_audio_path)

    # 1. Pitch accuracy (25%) — scalar similarity of mean pitch
    pitch_accuracy = _scalar_similarity(ref.pitch_mean_hz, cand.pitch_mean_hz)

    # 2. Tempo stability (20%) — BPM similarity + beat regularity similarity
    tempo_sim = _scalar_similarity(ref.tempo_bpm, cand.tempo_bpm)
    beat_reg_sim = _scalar_similarity(ref.beat_regularity, cand.beat_regularity)
    tempo_stability = (tempo_sim + beat_reg_sim) / 2.0

    # 3. Rhythm consistency (20%) — PyTorch cosine similarity of onset profiles
    rhythm_consistency = _cosine_sim_torch(ref.onset_profile, cand.onset_profile)

    # 4. Dynamics similarity (15%) — RMS energy comparison
    dynamics_similarity = _scalar_similarity(ref.rms_energy, cand.rms_energy)

    # 5. Timbre similarity (20%) — PyTorch cosine similarity of MFCC vectors
    timbre_similarity = _cosine_sim_torch(ref.mfcc_vector, cand.mfcc_vector)

    # Weighted aggregate
    # Weighted score follows project rubric and yields a normalized 0-100 mark.
    raw_score = (
        pitch_accuracy * 0.25
        + tempo_stability * 0.20
        + rhythm_consistency * 0.20
        + dynamics_similarity * 0.15
        + timbre_similarity * 0.20
    )
    score = round(float(max(0.0, min(100.0, raw_score * 100.0))), 2)

    duration_similarity = _scalar_similarity(ref.duration_seconds, cand.duration_seconds)

    return SimilarityAnalysis(
        score=score,
        pitch_accuracy=round(pitch_accuracy, 4),
        tempo_stability=round(tempo_stability, 4),
        rhythm_consistency=round(rhythm_consistency, 4),
        dynamics_similarity=round(dynamics_similarity, 4),
        timbre_similarity=round(timbre_similarity, 4),
        duration_similarity=round(duration_similarity, 4),
        energy_similarity=round(dynamics_similarity, 4),
        reference_tempo_bpm=round(ref.tempo_bpm, 2),
        candidate_tempo_bpm=round(cand.tempo_bpm, 2),
        reference_pitch_hz=round(ref.pitch_mean_hz, 2),
        candidate_pitch_hz=round(cand.pitch_mean_hz, 2),
    )
