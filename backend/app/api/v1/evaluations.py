"""Evaluation API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.evaluation import Evaluation
from app.models.user import User
from app.schemas.evaluation import (
    EvaluationCreate,
    EvaluationResponse,
    EvaluationUpdate,
    EvaluationWithPerformanceResponse,
)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("/", response_model=list[EvaluationWithPerformanceResponse])
async def get_evaluations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[Evaluation]:
    """Get evaluations for current user.

    For musicians: their own evaluations
    For evaluators: evaluations they've created
    For admins: all evaluations

    Args:
        skip: Number of evaluations to skip
        limit: Maximum number of evaluations to return
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of evaluations
    """
    query = db.query(Evaluation)

    if current_user.role.name == "musician":
        # Musicians see evaluations of their performances
        query = query.join(Evaluation.performance).filter(
            Evaluation.performance.has(musician_id=current_user.id)
        )
    elif current_user.role.name == "evaluator":
        # Evaluators see evaluations they've created
        query = query.filter(Evaluation.evaluator_id == current_user.id)
    # Admins see all evaluations (no filter)

    evaluations = query.offset(skip).limit(limit).all()
    return evaluations


@router.get("/{evaluation_id}", response_model=EvaluationWithPerformanceResponse)
async def get_evaluation(
    evaluation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Evaluation:
    """Get evaluation by ID.

    Args:
        evaluation_id: Evaluation ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Evaluation data

    Raises:
        HTTPException: If evaluation not found or access denied
    """
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()

    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found",
        )

    # Check permissions
    if current_user.role.name == "musician":
        if evaluation.performance.musician_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
    elif current_user.role.name == "evaluator":
        if evaluation.evaluator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
    # Admins can access all evaluations

    return evaluation


@router.post("/", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluation(
    evaluation_data: EvaluationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Evaluation:
    """Create a new evaluation (evaluators and admins only).

    Args:
        evaluation_data: Evaluation creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created evaluation

    Raises:
        HTTPException: If user doesn't have permission or performance not found
    """
    if current_user.role.name not in ["evaluator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only evaluators and admins can create evaluations",
        )

    # Check if performance exists
    from app.models.evaluation import Performance

    performance = (
        db.query(Performance).filter(Performance.id == evaluation_data.performance_id).first()
    )
    if not performance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Performance not found",
        )

    # Create evaluation
    evaluation = Evaluation(
        id=f"eval_{current_user.id}_{evaluation_data.performance_id}_{db.query(Evaluation).count() + 1}",
        performance_id=evaluation_data.performance_id,
        evaluator_id=current_user.id,
        score=evaluation_data.score,
        comments=evaluation_data.comments,
    )

    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.put("/{evaluation_id}", response_model=EvaluationResponse)
async def update_evaluation(
    evaluation_id: str,
    evaluation_update: EvaluationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Evaluation:
    """Update evaluation (evaluators and admins only).

    Args:
        evaluation_id: Evaluation ID
        evaluation_update: Evaluation update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated evaluation

    Raises:
        HTTPException: If evaluation not found or access denied
    """
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found",
        )

    # Check permissions
    if current_user.role.name not in ["evaluator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only evaluators and admins can update evaluations",
        )

    if current_user.role.name == "evaluator" and evaluation.evaluator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Update evaluation fields
    for field, value in evaluation_update.model_dump(exclude_unset=True).items():
        setattr(evaluation, field, value)

    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.delete("/{evaluation_id}")
async def delete_evaluation(
    evaluation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    """Delete evaluation (admins only).

    Args:
        evaluation_id: Evaluation ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: If evaluation not found or access denied
    """
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete evaluations",
        )

    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found",
        )

    db.delete(evaluation)
    db.commit()
    return {"message": "Evaluation deleted successfully"}
