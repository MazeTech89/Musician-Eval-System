"""Background worker entry points for performance analysis.

This module is intentionally lightweight for now; it exposes a callable that
can be wired to Celery tasks in a follow-up change.
"""

from app.core.database import SessionLocal
from sqlalchemy.orm import Session

from app.models.evaluation import Performance
from app.services.ai_analysis import AIAnalysisService


def run_performance_analysis(db: Session, performance_id: int):
    """Run analysis for a given performance id and return persisted result."""
    performance = db.query(Performance).filter(Performance.id == performance_id).first()
    if not performance:
        return None

    return AIAnalysisService.run_analysis(db, performance)


def process_performance_analysis(performance_id: int):
    """Process analysis in a background-safe session."""
    db = SessionLocal()
    try:
        performance = db.query(Performance).filter(Performance.id == performance_id).first()
        if not performance:
            return None

        return AIAnalysisService.run_analysis(db, performance)
    finally:
        db.close()
