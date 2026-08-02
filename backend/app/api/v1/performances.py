"""Performance API routes."""

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.audit import record_audit_event
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.evaluation import Evaluation, EvaluationStatus, Performance
from app.models.user import User
from app.schemas.evaluation import (
    PerformanceCreate,
    PerformanceResponse,
    PerformanceUpdate,
    SimilarityAnalysisResponse,
)
from app.services.audio_similarity import score_audio_similarity
from app.services.s3_storage import (
    S3StorageError,
    delete_audio_file,
    upload_performance_audio_to_s3,
)
from app.core.upload_security import validate_audio_upload

router = APIRouter(prefix="/performances", tags=["performances"])

def _resolve_local_audio_path(audio_file_url: str) -> Path:
    """Resolve a locally stored audio file path from the stored URL."""
    if not audio_file_url:
        raise ValueError("Performance has no audio file")

    if audio_file_url.startswith("s3://"):
        raise ValueError("Similarity analysis currently supports local uploads only")

    if audio_file_url.startswith("/uploads/"):
        upload_dir = Path(settings.local_upload_dir)
        if not upload_dir.is_absolute():
            upload_dir = Path.cwd() / upload_dir
        return upload_dir / Path(audio_file_url).name

    candidate_path = Path(audio_file_url)
    if not candidate_path.is_absolute():
        candidate_path = Path.cwd() / candidate_path
    return candidate_path


@router.get("/", response_model=list[PerformanceResponse])
async def get_performances(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[Performance]:
    """Get performances.

    For musicians: their own performances
    For evaluators/admins: all performances

    Args:
        skip: Number of performances to skip
        limit: Maximum number of performances to return
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of performances
    """
    query = db.query(Performance)

    if current_user.role.name == "musician":
        # Musicians see only their own performances
        query = query.filter(Performance.musician_id == current_user.id)
    # Admins and evaluators see all performances (no filter)

    performances = query.offset(skip).limit(limit).all()
    return performances


@router.get("/{performance_id}", response_model=PerformanceResponse)
async def get_performance(
    performance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Performance:
    """Get performance by ID.

    Args:
        performance_id: Performance ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Performance data

    Raises:
        HTTPException: If performance not found or access denied
    """
    performance = db.query(Performance).filter(Performance.id == performance_id).first()

    if not performance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Performance not found",
        )

    # Check permissions - musicians can only view their own
    if current_user.role.name == "musician":
        if performance.musician_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

    return performance


@router.post("/", response_model=PerformanceResponse, status_code=status.HTTP_201_CREATED)
async def create_performance(
    performance_data: PerformanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Performance:
    """Create a new performance (musicians and admins only).

    Args:
        performance_data: Performance creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created performance

    Raises:
        HTTPException: If user doesn't have permission
    """
    if current_user.role.name not in ["musician"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only musicians can create performances",
        )

    # Create performance
    performance = Performance(
        title=performance_data.title,
        description=performance_data.description,
        audio_file_url=performance_data.audio_file_url,
        musician_id=current_user.id,
        status="pending",
    )

    db.add(performance)
    db.commit()
    db.refresh(performance)
    return performance


@router.post(
    "/upload-audio",
    response_model=PerformanceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_performance_with_audio_upload(
    title: str = Form(...),
    description: str | None = Form(None),
    audio_file: UploadFile = File(...),  # noqa: B008
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Performance:
    """Upload an audio file to S3 and create a performance record."""
    if current_user.role.name not in ["musician"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only musicians can upload performances",
        )

    validate_audio_upload(audio_file)

    try:
        audio_file_url = upload_performance_audio_to_s3(
            audio_file=audio_file,
            musician_id=current_user.id,
        )
    except S3StorageError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(err),
        ) from err

    performance = Performance(
        title=title,
        description=description,
        audio_file_url=audio_file_url,
        musician_id=current_user.id,
        status="pending",
    )

    db.add(performance)
    db.commit()
    db.refresh(performance)
    record_audit_event(
        "performance.uploaded",
        performance_id=performance.id,
        user_id=current_user.id,
        username=current_user.username,
    )
    return performance


@router.post(
    "/{performance_id}/analyze-audio",
    response_model=SimilarityAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
async def analyze_performance_audio(
    performance_id: int,
    reference_audio: UploadFile = File(...),  # noqa: B008
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, object]:
    """Create a similarity evaluation by comparing a performance against a reference audio file."""
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can analyze performances",
        )

    performance = db.query(Performance).filter(Performance.id == performance_id).first()
    if not performance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Performance not found",
        )

    if not performance.audio_file_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Performance has no uploaded audio to compare",
        )

    validate_audio_upload(reference_audio)
    reference_bytes = await reference_audio.read()
    if not reference_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reference audio was empty",
        )

    suffix = Path(reference_audio.filename or "reference.wav").suffix.lower() or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_reference:
        tmp_reference.write(reference_bytes)
        temp_reference_path = Path(tmp_reference.name)

    try:
        candidate_audio_path = _resolve_local_audio_path(performance.audio_file_url)
        if not candidate_audio_path.exists():
            raise FileNotFoundError(candidate_audio_path)

        analysis = score_audio_similarity(candidate_audio_path, temp_reference_path)
    except FileNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Performance audio file could not be found",
        ) from err
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err
    finally:
        if temp_reference_path.exists():
            temp_reference_path.unlink(missing_ok=True)

    evaluation = Evaluation(
        performance_id=performance.id,
        evaluator_id=current_user.id,
        score=analysis.score,
        comments=(
            "Auto-generated similarity analysis against "
            f"{reference_audio.filename or 'reference audio'}"
        ),
        status=EvaluationStatus.COMPLETED,
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    record_audit_event(
        "performance.analyzed",
        performance_id=performance.id,
        evaluation_id=evaluation.id,
        user_id=current_user.id,
        username=current_user.username,
    )

    return {
        "performance_id": performance.id,
        "score": analysis.score,
        "reference_filename": reference_audio.filename or "reference.wav",
        "created_evaluation_id": evaluation.id,
        "breakdown": {
            "pitch_accuracy": analysis.pitch_accuracy,
            "tempo_stability": analysis.tempo_stability,
            "rhythm_consistency": analysis.rhythm_consistency,
            "dynamics_similarity": analysis.dynamics_similarity,
            "timbre_similarity": analysis.timbre_similarity,
            "duration_similarity": analysis.duration_similarity,
            "energy_similarity": analysis.energy_similarity,
            "reference_tempo_bpm": analysis.reference_tempo_bpm,
            "candidate_tempo_bpm": analysis.candidate_tempo_bpm,
            "reference_pitch_hz": analysis.reference_pitch_hz,
            "candidate_pitch_hz": analysis.candidate_pitch_hz,
        },
    }


@router.put("/{performance_id}", response_model=PerformanceResponse)
async def update_performance(
    performance_id: int,
    performance_update: PerformanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Performance:
    """Update performance (owner or admin only).

    Args:
        performance_id: Performance ID
        performance_update: Performance update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated performance

    Raises:
        HTTPException: If performance not found or access denied
    """
    performance = db.query(Performance).filter(Performance.id == performance_id).first()
    if not performance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Performance not found",
        )

    # Check permissions
    if current_user.role.name == "musician":
        if performance.musician_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
    elif current_user.role.name not in ["admin", "moderator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update performances",
        )

    # Update performance fields
    update_data = performance_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(performance, field, value)

    db.commit()
    db.refresh(performance)
    return performance


@router.delete("/{performance_id}")
async def delete_performance(
    performance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    """Delete performance (owner or admin only).

    Args:
        performance_id: Performance ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: If performance not found or access denied
    """
    performance = db.query(Performance).filter(Performance.id == performance_id).first()
    if not performance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Performance not found",
        )

    # Check permissions - only owner or admin can delete
    if current_user.role.name == "musician":
        if performance.musician_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
    elif current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete performances",
        )

    audio_file_url = performance.audio_file_url
    delete_audio_file(audio_file_url)
    db.query(Evaluation).filter(Evaluation.performance_id == performance.id).delete(
        synchronize_session=False
    )
    db.delete(performance)
    db.commit()
    record_audit_event(
        "performance.deleted",
        performance_id=performance_id,
        user_id=current_user.id,
        username=current_user.username,
    )
    return {"message": "Performance deleted successfully"}
