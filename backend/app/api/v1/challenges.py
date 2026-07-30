"""Reference track, assignment, and submission routes."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.challenge import AnalysisResult, Assignment, ReferenceTrack, Submission
from app.models.user import User
from app.schemas.challenge import (
    AssignmentCreate,
    AssignmentResponse,
    ReferenceTrackResponse,
    SubmissionResponse,
)
from app.services.s3_storage import S3StorageError, upload_audio_to_s3

router = APIRouter(prefix="/challenges", tags=["challenges"])

ALLOWED_AUDIO_CONTENT_TYPES = {
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
    "audio/ogg",
    "audio/webm",
    "audio/mp4",
    "audio/flac",
}


def _role_value(user: User) -> str:
    role_name = getattr(user.role, "name", user.role)
    if hasattr(role_name, "value"):
        return role_name.value
    return str(role_name).lower()


@router.post("/reference-tracks", response_model=ReferenceTrackResponse, status_code=status.HTTP_201_CREATED)
async def create_reference_track(
    title: str = Form(...),
    description: str | None = Form(None),
    audio_file: UploadFile = File(...),  # noqa: B008
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ReferenceTrack:
    """Upload an original song for later replication."""
    if _role_value(current_user) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can upload reference tracks",
        )

    if audio_file.content_type not in ALLOWED_AUDIO_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported audio file type",
        )

    try:
        audio_file_url = upload_audio_to_s3(audio_file=audio_file, owner_id=current_user.id, collection="reference-tracks")
    except S3StorageError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(err),
        ) from err

    reference_track = ReferenceTrack(
        title=title,
        description=description,
        audio_file_url=audio_file_url,
        uploaded_by_id=current_user.id,
    )

    db.add(reference_track)
    db.commit()
    db.refresh(reference_track)
    return reference_track


@router.get("/reference-tracks", response_model=list[ReferenceTrackResponse])
async def list_reference_tracks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ReferenceTrack]:
    """List reference tracks visible to the current user."""
    query = db.query(ReferenceTrack)
    if _role_value(current_user) != "admin":
        query = query.filter(ReferenceTrack.uploaded_by_id == current_user.id)
    return query.order_by(ReferenceTrack.created_at.desc()).all()


@router.post("/assignments", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    assignment_data: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Assignment:
    """Create an assignment tied to a reference track."""
    if _role_value(current_user) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create assignments",
        )

    reference_track = (
        db.query(ReferenceTrack)
        .filter(ReferenceTrack.id == assignment_data.reference_track_id)
        .first()
    )
    if not reference_track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reference track not found",
        )

    assignment = Assignment(
        title=assignment_data.title,
        description=assignment_data.description,
        reference_track_id=assignment_data.reference_track_id,
        created_by_id=current_user.id,
        target_role=assignment_data.target_role,
        due_at=assignment_data.due_at,
        is_active=assignment_data.is_active,
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/assignments", response_model=list[AssignmentResponse])
async def list_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[Assignment]:
    """List assignments available to the current user."""
    query = db.query(Assignment)
    if _role_value(current_user) == "admin":
        return query.order_by(Assignment.created_at.desc()).all()

    return (
        query.filter(Assignment.is_active.is_(True))
        .filter(Assignment.target_role == _role_value(current_user))
        .order_by(Assignment.created_at.desc())
        .all()
    )


@router.post(
    "/assignments/{assignment_id}/submit",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_assignment_audio(
    assignment_id: int,
    notes: str | None = Form(None),
    audio_file: UploadFile = File(...),  # noqa: B008
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Submission:
    """Upload a musician recording for a specific assignment."""
    if _role_value(current_user) not in {"musician", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only musicians and admins can submit recordings",
        )

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment or not assignment.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    if _role_value(current_user) != "admin" and assignment.target_role != _role_value(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This assignment is not available for your role",
        )

    if audio_file.content_type not in ALLOWED_AUDIO_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported audio file type",
        )

    try:
        audio_file_url = upload_audio_to_s3(
            audio_file=audio_file,
            owner_id=current_user.id,
            collection="submissions",
        )
    except S3StorageError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(err),
        ) from err

    submission = Submission(
        assignment_id=assignment_id,
        musician_id=current_user.id,
        audio_file_url=audio_file_url,
        notes=notes,
        status="pending_analysis",
    )

    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.get("/submissions", response_model=list[SubmissionResponse])
async def list_submissions(
    assignment_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[Submission]:
    """List submissions for the current user or all submissions for admins."""
    query = db.query(Submission)
    if assignment_id is not None:
        query = query.filter(Submission.assignment_id == assignment_id)

    if _role_value(current_user) != "admin":
        query = query.filter(Submission.musician_id == current_user.id)

    return query.order_by(Submission.created_at.desc()).all()


@router.post("/submissions/{submission_id}/analyze", response_model=SubmissionResponse)
async def store_analysis_result(
    submission_id: int,
    similarity_score: float = Form(...),
    summary: str | None = Form(None),
    metrics_json: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Submission:
    """Store a manual analysis result placeholder for a submission."""
    if _role_value(current_user) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can store analysis results",
        )

    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    analysis_result = (
        db.query(AnalysisResult).filter(AnalysisResult.submission_id == submission_id).first()
    )
    if not analysis_result:
        analysis_result = AnalysisResult(
            submission_id=submission_id,
            reference_track_id=submission.assignment.reference_track_id,
            similarity_score=similarity_score,
            metrics_json=metrics_json,
            summary=summary,
        )
        db.add(analysis_result)
    else:
        analysis_result.similarity_score = similarity_score
        analysis_result.metrics_json = metrics_json
        analysis_result.summary = summary

    submission.status = "analyzed"
    submission.similarity_score = similarity_score

    db.commit()
    db.refresh(submission)
    return submission
