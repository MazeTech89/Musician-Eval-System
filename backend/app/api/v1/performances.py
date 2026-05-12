"""Performance API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.evaluation import Performance
from app.models.user import User
from app.schemas.evaluation import (
    PerformanceCreate,
    PerformanceResponse,
    PerformanceUpdate,
)

router = APIRouter(prefix="/performances", tags=["performances"])


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
    if current_user.role.name not in ["musician", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only musicians and admins can create performances",
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

    db.delete(performance)
    db.commit()
    return {"message": "Performance deleted successfully"}