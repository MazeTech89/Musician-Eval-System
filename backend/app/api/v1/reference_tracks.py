"""Reference tracks and assignments API routes."""

import logging
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.audit import record_audit_event
from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.core.dependencies import ensure_admin_mfa_verified, get_current_active_user
from app.core.upload_security import validate_audio_upload
from app.models.evaluation import Evaluation, EvaluationStatus, Performance
from app.models.reference_track import Assignment, ReferenceTrack
from app.models.user import User
from app.schemas.evaluation import SimilarityAnalysisResponse
from app.schemas.reference_tracks import (
    AssignmentSubmissionResponse,
    AssignmentWithReferenceResponse,
    ReferenceTrackResponse,
)
from app.services.audio_similarity import score_audio_similarity
from app.services.s3_storage import (
    S3StorageError,
    delete_audio_file,
    get_storage_health,
    materialize_audio_file,
    upload_performance_audio_to_s3,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["reference-tracks"])


def _assignment_visible_to_musician(assignment: Assignment, musician: User) -> bool:
    """A musician can see/submit to a task only if it targets them (or targets nobody specific)."""
    if assignment.target_musician_id is not None and assignment.target_musician_id != musician.id:
        return False
    if assignment.target_instrument_type:
        musician_instrument = (musician.instrument_type or "").strip().lower()
        if musician_instrument != assignment.target_instrument_type.strip().lower():
            return False
    return True


def _resolve_target_musician_id(db: Session, target_musician_id: int | None) -> int | None:
    """Validate an optional target musician ID; 0 clears targeting to 'no specific musician'."""
    if not target_musician_id:
        return None
    target_user = db.query(User).filter(User.id == target_musician_id).first()
    if not target_user or target_user.role.name != "musician":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="target_musician_id must reference an existing musician",
        )
    return target_user.id


@router.get("/reference-tracks/storage-health")
async def get_reference_storage_health(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str | bool]:
    """Report whether the active audio storage backend is reachable."""
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view storage health",
        )
    ensure_admin_mfa_verified(current_user)

    return get_storage_health()


def _resolve_local_audio_path(audio_file_url: str) -> Path:
    """Resolve a locally stored audio file path from the stored URL."""
    if not audio_file_url:
        raise ValueError("Audio file is missing")

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


def _materialize_and_score(assignment: Assignment, performance: Performance) -> object:
    """Resolve both audio files locally and compute similarity.

    Raises S3StorageError, ValueError, or FileNotFoundError on failure.
    """
    # Materialize both audio URLs as local filesystem paths:
    # - local URLs resolve directly
    # - S3 URLs are downloaded to temporary files
    reference_audio_path, reference_is_temporary = materialize_audio_file(
        assignment.reference_track.audio_file_url
    )
    candidate_audio_path, candidate_is_temporary = materialize_audio_file(
        performance.audio_file_url
    )
    try:
        # Validate both files still exist before running feature extraction/scoring.
        if not reference_audio_path.exists() or not candidate_audio_path.exists():
            raise FileNotFoundError

        return score_audio_similarity(reference_audio_path, candidate_audio_path)
    finally:
        # Temporary files are only created for S3 downloads and must be cleaned up.
        if reference_is_temporary:
            reference_audio_path.unlink(missing_ok=True)
        if candidate_is_temporary:
            candidate_audio_path.unlink(missing_ok=True)


def _score_assignment_performance(
    db: Session,
    assignment: Assignment,
    performance: Performance,
    current_user: User,
) -> tuple[object, Evaluation]:
    """Score a performance against an assignment reference track (synchronous, admin re-analyze only)."""
    # Guardrails: scoring requires both uploaded candidate audio and a task reference.
    if not performance.audio_file_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Performance has no uploaded audio to compare",
        )

    if not assignment.reference_track or not assignment.reference_track.audio_file_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment has no reference audio track",
        )

    try:
        analysis = _materialize_and_score(assignment, performance)
    except S3StorageError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(err),
        ) from err
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err
    except FileNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file could not be found",
        ) from err

    performance.assignment_id = assignment.id
    evaluation = Evaluation(
        performance_id=performance.id,
        evaluator_id=current_user.id,
        score=analysis.score,
        comments=(
            "Auto-generated similarity analysis against " f"{assignment.reference_track.title}"
        ),
        status=EvaluationStatus.COMPLETED,
    )
    db.add(evaluation)

    return analysis, evaluation


def _score_submission_in_background(
    assignment_id: int, performance_id: int, evaluation_id: int
) -> None:
    """Run similarity scoring outside the request/response cycle.

    Uses its own DB session since the request-scoped session is closed by
    the time this runs. Never raises: failures are recorded on the
    evaluation row so the frontend can surface them via polling.
    """
    db = SessionLocal()
    try:
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        performance = db.query(Performance).filter(Performance.id == performance_id).first()
        evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not assignment or not performance or not evaluation:
            logger.error(
                "Background scoring skipped: missing record(s) for evaluation %s",
                evaluation_id,
            )
            return

        try:
            analysis = _materialize_and_score(assignment, performance)
        except FileNotFoundError:
            evaluation.comments = (
                "Upload succeeded, but automatic scoring failed because the "
                "assignment reference audio file could not be found. Ask an admin "
                "to replace the reference audio in Reference Upload, then re-run scoring."
            )
            db.commit()
            return
        except (S3StorageError, ValueError) as err:
            evaluation.comments = f"Automatic scoring failed: {err}"
            evaluation.status = EvaluationStatus.CANCELLED
            db.commit()
            return

        performance.assignment_id = assignment.id
        evaluation.score = analysis.score
        evaluation.comments = (
            f"Auto-generated similarity analysis against {assignment.reference_track.title}"
        )
        evaluation.status = EvaluationStatus.COMPLETED
        db.commit()
        record_audit_event(
            "assignment.submission.scored",
            assignment_id=assignment_id,
            performance_id=performance_id,
            evaluation_id=evaluation_id,
            score=analysis.score,
        )
    except Exception:  # noqa: BLE001 - background task must never raise
        logger.exception("Background scoring crashed for evaluation %s", evaluation_id)
        db.rollback()
        evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if evaluation:
            evaluation.status = EvaluationStatus.CANCELLED
            evaluation.comments = "Automatic scoring failed due to an internal error."
            db.commit()
    finally:
        db.close()


@router.get("/reference-tracks", response_model=list[ReferenceTrackResponse])
async def list_reference_tracks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ReferenceTrack]:
    """List reusable reference tracks."""
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view reference tracks",
        )
    ensure_admin_mfa_verified(current_user)

    return (
        db.query(ReferenceTrack)
        .filter(ReferenceTrack.is_active.is_(True))
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.post(
    "/reference-tracks",
    response_model=ReferenceTrackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_reference_track(
    title: str = Form(...),
    description: str | None = Form(None),
    audio_file: UploadFile = File(...),  # noqa: B008
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ReferenceTrack:
    """Create a reusable reference track for later assignments."""
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create reference tracks",
        )
    ensure_admin_mfa_verified(current_user)

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

    reference_track = ReferenceTrack(
        title=title,
        description=description,
        audio_file_url=audio_file_url,
        created_by_id=current_user.id,
        is_active=True,
    )
    db.add(reference_track)
    db.commit()
    db.refresh(reference_track)
    record_audit_event(
        "reference_track.created",
        reference_track_id=reference_track.id,
        user_id=current_user.id,
        username=current_user.username,
    )
    return reference_track


@router.get("/reference-tracks/{reference_track_id}", response_model=ReferenceTrackResponse)
async def get_reference_track(
    reference_track_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ReferenceTrack:
    """Get one reference track by ID."""
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view reference tracks",
        )
    ensure_admin_mfa_verified(current_user)

    reference_track = (
        db.query(ReferenceTrack).filter(ReferenceTrack.id == reference_track_id).first()
    )
    if not reference_track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reference track not found"
        )

    if not reference_track.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reference track not found"
        )

    return reference_track


@router.put("/reference-tracks/{reference_track_id}", response_model=ReferenceTrackResponse)
async def update_reference_track(
    reference_track_id: int,
    title: str | None = Form(None),
    description: str | None = Form(None),
    is_active: bool | None = Form(None),
    audio_file: UploadFile | None = File(None),  # noqa: B008
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ReferenceTrack:
    """Update a reference track."""
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update reference tracks",
        )
    ensure_admin_mfa_verified(current_user)

    reference_track = (
        db.query(ReferenceTrack).filter(ReferenceTrack.id == reference_track_id).first()
    )
    if not reference_track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reference track not found"
        )

    if title is not None:
        reference_track.title = title
    if description is not None:
        reference_track.description = description
    if is_active is not None:
        reference_track.is_active = is_active

    if audio_file is not None:
        validate_audio_upload(audio_file)

        try:
            reference_track.audio_file_url = upload_performance_audio_to_s3(
                audio_file=audio_file,
                musician_id=current_user.id,
            )
        except S3StorageError as err:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(err),
            ) from err

    db.commit()
    db.refresh(reference_track)
    record_audit_event(
        "reference_track.updated",
        reference_track_id=reference_track.id,
        user_id=current_user.id,
        username=current_user.username,
    )
    return reference_track


@router.delete("/reference-tracks/{reference_track_id}")
async def delete_reference_track(
    reference_track_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    """Delete a reference track."""
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete reference tracks",
        )
    ensure_admin_mfa_verified(current_user)

    reference_track = (
        db.query(ReferenceTrack).filter(ReferenceTrack.id == reference_track_id).first()
    )
    if not reference_track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reference track not found"
        )

    if reference_track.assignments:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reference track is used by assignments. Delete those assignments first.",
        )

    delete_audio_file(reference_track.audio_file_url)
    db.delete(reference_track)
    db.commit()
    record_audit_event(
        "reference_track.deleted",
        reference_track_id=reference_track_id,
        user_id=current_user.id,
        username=current_user.username,
    )
    return {"message": "Reference track deleted successfully"}


@router.get("/assignments", response_model=list[AssignmentWithReferenceResponse])
async def list_assignments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[Assignment]:
    """List assignments."""
    if current_user.role.name not in ["admin", "evaluator", "musician"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins, evaluators, and musicians can view assignments",
        )

    query = db.query(Assignment).filter(Assignment.is_active.is_(True))

    if current_user.role.name == "musician":
        instrument = (current_user.instrument_type or "").strip()
        conditions = [
            and_(
                Assignment.target_musician_id.is_(None),
                Assignment.target_instrument_type.is_(None),
            ),
            Assignment.target_musician_id == current_user.id,
        ]
        if instrument:
            conditions.append(Assignment.target_instrument_type.ilike(instrument))
        query = query.filter(or_(*conditions))

    return query.offset(skip).limit(limit).all()


@router.post(
    "/assignments",
    response_model=AssignmentWithReferenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_assignment(
    title: str = Form(...),
    description: str | None = Form(None),
    reference_track_id: int = Form(...),
    target_musician_id: int | None = Form(None),
    target_instrument_type: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Assignment:
    """Create an assignment bound to a reference track."""
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create assignments",
        )
    ensure_admin_mfa_verified(current_user)

    reference_track = (
        db.query(ReferenceTrack)
        .filter(ReferenceTrack.id == reference_track_id)
        .filter(ReferenceTrack.is_active.is_(True))
        .first()
    )
    if not reference_track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reference track not found"
        )

    assignment = Assignment(
        title=title,
        description=description,
        reference_track_id=reference_track.id,
        created_by_id=current_user.id,
        target_musician_id=_resolve_target_musician_id(db, target_musician_id),
        target_instrument_type=(target_instrument_type or "").strip() or None,
        is_active=True,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/assignments/{assignment_id}", response_model=AssignmentWithReferenceResponse)
async def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Assignment:
    """Get one assignment by ID."""
    if current_user.role.name not in ["admin", "evaluator", "musician"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins, evaluators, and musicians can view assignments",
        )

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    if not assignment.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    if current_user.role.name == "musician" and not _assignment_visible_to_musician(
        assignment, current_user
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    return assignment


@router.put("/assignments/{assignment_id}", response_model=AssignmentWithReferenceResponse)
async def update_assignment(
    assignment_id: int,
    title: str | None = Form(None),
    description: str | None = Form(None),
    reference_track_id: int | None = Form(None),
    is_active: bool | None = Form(None),
    target_musician_id: int | None = Form(None),
    target_instrument_type: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Assignment:
    """Update an assignment."""
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update assignments",
        )
    ensure_admin_mfa_verified(current_user)

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    if title is not None:
        assignment.title = title
    if description is not None:
        assignment.description = description
    if is_active is not None:
        assignment.is_active = is_active
    if target_musician_id is not None:
        assignment.target_musician_id = _resolve_target_musician_id(db, target_musician_id)
    if target_instrument_type is not None:
        assignment.target_instrument_type = target_instrument_type.strip() or None
    if reference_track_id is not None:
        reference_track = (
            db.query(ReferenceTrack)
            .filter(ReferenceTrack.id == reference_track_id)
            .filter(ReferenceTrack.is_active.is_(True))
            .first()
        )
        if not reference_track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reference track not found"
            )
        assignment.reference_track_id = reference_track.id

    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/assignments/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    """Delete an assignment."""
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete assignments",
        )
    ensure_admin_mfa_verified(current_user)

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    for performance in assignment.performances:
        performance.assignment_id = None

    db.delete(assignment)
    db.commit()
    record_audit_event(
        "assignment.deleted",
        assignment_id=assignment_id,
        user_id=current_user.id,
        username=current_user.username,
    )
    return {"message": "Assignment deleted successfully"}


@router.post(
    "/assignments/{assignment_id}/submissions",
    response_model=AssignmentSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_performance_for_assignment(
    assignment_id: int,
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: str | None = Form(None),
    audio_file: UploadFile = File(...),  # noqa: B008
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, object]:
    """Create a performance submission against an assignment and score it in the background.

    Scoring runs librosa/torch analysis that can take well over a minute for
    longer recordings, which exceeds the proxy/edge timeout in production and
    breaks the response before it can be returned. Instead, the request
    returns immediately with a pending evaluation, and the heavy analysis
    runs as a background task; the frontend polls the evaluation for the
    final score.
    """
    if current_user.role.name not in ["musician"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only musicians can submit performances",
        )

    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id)
        .filter(Assignment.is_active.is_(True))
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    if not _assignment_visible_to_musician(assignment, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    # Enforce upload security checks before writing any bytes to storage.
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

    # Persist submission first so any evaluation rows can reference a stable performance ID.
    performance = Performance(
        title=title,
        description=description,
        audio_file_url=audio_file_url,
        musician_id=current_user.id,
        assignment_id=assignment.id,
        status="pending",
    )
    db.add(performance)
    db.flush()

    # Scoring runs out-of-band so heavy librosa/torch analysis can't time out the upload request.
    evaluation = Evaluation(
        performance_id=performance.id,
        evaluator_id=current_user.id,
        score=None,
        comments="Automatic scoring is running in the background.",
        status=EvaluationStatus.PENDING,
    )
    db.add(evaluation)
    db.commit()
    db.refresh(performance)
    db.refresh(evaluation)

    background_tasks.add_task(
        _score_submission_in_background,
        assignment_id=assignment.id,
        performance_id=performance.id,
        evaluation_id=evaluation.id,
    )

    record_audit_event(
        "assignment.submission.created",
        assignment_id=assignment.id,
        performance_id=performance.id,
        evaluation_id=evaluation.id,
        user_id=current_user.id,
        username=current_user.username,
        scoring_pending=True,
    )

    # Return the persisted entities immediately; analysis is filled in later via polling.
    return {
        "performance": performance,
        "evaluation": evaluation,
        "analysis": None,
        "message": "Upload succeeded. Scoring is running in the background — check back shortly.",
    }


@router.post(
    "/assignments/{assignment_id}/performances/{performance_id}/analyze",
    response_model=SimilarityAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
async def analyze_performance_with_assignment(
    assignment_id: int,
    performance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, object]:
    """Analyze a performance using the reference track from an assignment."""
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can analyze performances",
        )
    ensure_admin_mfa_verified(current_user)

    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id)
        .filter(Assignment.is_active.is_(True))
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    performance = db.query(Performance).filter(Performance.id == performance_id).first()
    if not performance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Performance not found")

    # Re-run deterministic scoring for an existing task/performance pair.
    analysis, evaluation = _score_assignment_performance(
        db=db,
        assignment=assignment,
        performance=performance,
        current_user=current_user,
    )
    db.commit()
    db.refresh(evaluation)
    db.refresh(performance)
    record_audit_event(
        "assignment.performance.analyzed",
        assignment_id=assignment.id,
        performance_id=performance.id,
        evaluation_id=evaluation.id,
        user_id=current_user.id,
        username=current_user.username,
    )

    return {
        "performance_id": performance.id,
        "score": analysis.score,
        "reference_filename": assignment.reference_track.title,
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


@router.get("/assignments/recommendations")
async def get_task_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[dict[str, Any]]:
    """Return each active task with its highest-scoring musician (admin only).

    For every active assignment this returns:
    - assignment metadata
    - total number of submissions
    - the best musician so far (highest completed evaluation score)
    """
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view task recommendations",
        )
    ensure_admin_mfa_verified(current_user)

    # Build recommendations only from active tasks.
    assignments = db.query(Assignment).filter(Assignment.is_active.is_(True)).all()

    recommendations = []
    for assignment in assignments:
        # Submission count gives admins quick participation visibility per task.
        total_submissions = (
            db.query(Performance).filter(Performance.assignment_id == assignment.id).count()
        )

        # Best completed evaluation for this assignment
        best_row = (
            db.query(Performance, Evaluation, User)
            .join(Evaluation, Evaluation.performance_id == Performance.id)
            .join(User, User.id == Performance.musician_id)
            .filter(Performance.assignment_id == assignment.id)
            .filter(Evaluation.score.isnot(None))
            .filter(Evaluation.status == EvaluationStatus.COMPLETED)
            .order_by(Evaluation.score.desc())
            .first()
        )

        # Keep response shape stable by returning null when no completed score exists yet.
        best_musician = None
        if best_row:
            _perf, best_eval, best_user = best_row
            best_musician = {
                "id": best_user.id,
                "username": best_user.username,
                "first_name": best_user.first_name,
                "last_name": best_user.last_name,
                "instrument_type": best_user.instrument_type,
                "skill_level": best_user.skill_level,
                "score": best_eval.score,
                "evaluation_id": best_eval.id,
            }

        recommendations.append(
            {
                "assignment_id": assignment.id,
                "assignment_title": assignment.title,
                "description": assignment.description,
                "reference_track_title": (
                    assignment.reference_track.title if assignment.reference_track else None
                ),
                "total_submissions": total_submissions,
                "best_musician": best_musician,
            }
        )

    return recommendations
