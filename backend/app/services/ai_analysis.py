"""AI analysis service for musician performances.

This module provides a deterministic baseline scorer so the end-to-end
analysis workflow can be exercised before plugging in real DSP/ML models.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.evaluation import AnalysisStatus, Performance, PerformanceAnalysis


class AIAnalysisService:
    """Service for creating and running performance analysis jobs."""

    @staticmethod
    def get_or_create_analysis(db: Session, performance: Performance) -> PerformanceAnalysis:
        """Get existing analysis row or create a pending one."""
        analysis = (
            db.query(PerformanceAnalysis)
            .filter(PerformanceAnalysis.performance_id == performance.id)
            .first()
        )
        if analysis:
            return analysis

        analysis = PerformanceAnalysis(
            performance_id=performance.id,
            status=AnalysisStatus.PENDING,
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis

    @staticmethod
    def queue_analysis(db: Session, performance: Performance) -> PerformanceAnalysis:
        """Create or reset an analysis row in queued state."""
        analysis = AIAnalysisService.get_or_create_analysis(db, performance)
        analysis.status = AnalysisStatus.PENDING
        analysis.error_message = None
        analysis.analyzed_at = None
        analysis.technique_score = None
        analysis.timing_score = None
        analysis.intonation_score = None
        analysis.overall_ai_score = None
        analysis.ai_feedback = None
        db.commit()
        db.refresh(analysis)
        return analysis

    @staticmethod
    def run_analysis(db: Session, performance: Performance) -> PerformanceAnalysis:
        """Run deterministic scoring and persist results.

        The current version uses a hash-based pseudo-score so we can ship the
        full pipeline now and swap in model-based scoring in a later iteration.
        """
        analysis = AIAnalysisService.get_or_create_analysis(db, performance)
        analysis.status = AnalysisStatus.RUNNING
        analysis.error_message = None
        db.commit()

        try:
            signal = "|".join(
                [
                    performance.title or "",
                    performance.description or "",
                    performance.audio_file_url or "",
                    str(performance.musician_id),
                ]
            )
            digest = hashlib.sha256(signal.encode("utf-8")).hexdigest()

            # Split digest into stable score buckets in [60, 100].
            technique = 60 + int(digest[0:8], 16) % 41
            timing = 60 + int(digest[8:16], 16) % 41
            intonation = 60 + int(digest[16:24], 16) % 41
            overall = round((technique + timing + intonation) / 3, 2)

            analysis.technique_score = float(technique)
            analysis.timing_score = float(timing)
            analysis.intonation_score = float(intonation)
            analysis.overall_ai_score = overall
            analysis.ai_feedback = (
                f"AI baseline feedback: strong technique ({technique:.0f}), "
                f"timing ({timing:.0f}), and intonation ({intonation:.0f}). "
                "Use this as an initial score before evaluator review."
            )
            analysis.analyzed_at = datetime.now(UTC)
            analysis.status = AnalysisStatus.COMPLETED
            analysis.error_message = None
            db.commit()
            db.refresh(analysis)
            return analysis
        except Exception as exc:
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = str(exc)
            db.commit()
            db.refresh(analysis)
            return analysis
