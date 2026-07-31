"""Reference tracks and assignments API routes."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.evaluation import Evaluation, EvaluationStatus, Performance
from app.models.reference_track import Assignment, ReferenceTrack
from app.models.user import User
from app.schemas.evaluation import SimilarityAnalysisResponse
from app.schemas.reference_tracks import (
    AssignmentWithReferenceResponse,
    ReferenceTrackResponse,
)
from app.services.audio_similarity import score_audio_similarity
from app.services.s3_storage import S3StorageError, upload_performance_audio_to_s3

router = APIRouter(tags=["reference-tracks"])

ALLOWED_AUDIO_CONTENT_TYPES = {
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
    "audio/ogg",
    "audio/webm",
    "audio/mp4",
    "audio/flac",
}


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


@router.get("/reference-tracks", response_model=list[ReferenceTrackResponse])
async def list_reference_tracks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ReferenceTrack]:
    """List reusable reference tracks."""
    if current_user.role.name not in ["admin", "evaluator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and evaluators can view reference tracks",
        )

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

    if audio_file.content_type not in ALLOWED_AUDIO_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported audio file type",
        )

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
    return reference_track


@router.get("/reference-tracks/{reference_track_id}", response_model=ReferenceTrackResponse)
async def get_reference_track(
    reference_track_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ReferenceTrack:
    """Get one reference track by ID."""
    if current_user.role.name not in ["admin", "evaluator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and evaluators can view reference tracks",
        )

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
        if audio_file.content_type not in ALLOWED_AUDIO_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported audio file type",
            )

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

    reference_track = (
        db.query(ReferenceTrack).filter(ReferenceTrack.id == reference_track_id).first()
    )
    if not reference_track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reference track not found"
        )

    db.delete(reference_track)
    db.commit()
    return {"message": "Reference track deleted successfully"}


@router.get("/assignments", response_model=list[AssignmentWithReferenceResponse])
async def list_assignments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[Assignment]:
    """List assignments."""
    if current_user.role.name not in ["admin", "evaluator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and evaluators can view assignments",
        )

    return (
        db.query(Assignment).filter(Assignment.is_active.is_(True)).offset(skip).limit(limit).all()
    )


@router.post(
    "/assignments",
    response_model=AssignmentWithReferenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_assignment(
    title: str = Form(...),
    description: str | None = Form(None),
    reference_track_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Assignment:
    """Create an assignment bound to a reference track."""
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create assignments",
        )

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
    if current_user.role.name not in ["admin", "evaluator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and evaluators can view assignments",
        )

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    if not assignment.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    return assignment


@router.put("/assignments/{assignment_id}", response_model=AssignmentWithReferenceResponse)
async def update_assignment(
    assignment_id: int,
    title: str | None = Form(None),
    description: str | None = Form(None),
    reference_track_id: int | None = Form(None),
    is_active: bool | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Assignment:
    """Update an assignment."""
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update assignments",
        )

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    if title is not None:
        assignment.title = title
    if description is not None:
        assignment.description = description
    if is_active is not None:
        assignment.is_active = is_active
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

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    db.delete(assignment)
    db.commit()
    return {"message": "Assignment deleted successfully"}


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
    if current_user.role.name not in ["admin", "evaluator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and evaluators can analyze performances",
        )

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
        reference_audio_path = _resolve_local_audio_path(assignment.reference_track.audio_file_url)
        candidate_audio_path = _resolve_local_audio_path(performance.audio_file_url)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    if not reference_audio_path.exists() or not candidate_audio_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file could not be found",
        )

    try:
        analysis = score_audio_similarity(reference_audio_path, candidate_audio_path)
    except FileNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file could not be found",
        ) from err
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
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
    db.commit()
    db.refresh(evaluation)
    db.refresh(performance)

    return {
        "performance_id": performance.id,
        "score": analysis.score,
        "reference_filename": assignment.reference_track.title,
        "created_evaluation_id": evaluation.id,
        "breakdown": {
            "duration_similarity": analysis.duration_similarity,
            "energy_similarity": analysis.energy_similarity,
            "peak_similarity": analysis.peak_similarity,
            "zero_crossing_similarity": analysis.zero_crossing_similarity,
            "histogram_similarity": analysis.histogram_similarity,
            "delta_profile_similarity": analysis.delta_profile_similarity,
        },
    }
