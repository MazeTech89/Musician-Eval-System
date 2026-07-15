"""Tests for AI performance analysis workflow."""

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.evaluation import Performance
from app.models.user import Role, RoleEnum, User
from app.services.ai_analysis import AIAnalysisService

client = TestClient(app)


def _ensure_role(db, role_name: RoleEnum) -> Role:
    role = db.query(Role).filter(Role.name == role_name).first()
    if role:
        return role

    role = Role(name=role_name, description=f"{role_name.value} role")
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def _ensure_musician_user(db) -> User:
    role = _ensure_role(db, RoleEnum.MUSICIAN)
    user = db.query(User).filter(User.username == "analysis_musician").first()
    if user:
        user.role_id = role.id
        user.is_active = True
        db.commit()
        db.refresh(user)
        return user

    user = User(
        username="analysis_musician",
        email="analysis_musician@example.com",
        hashed_password=hash_password("testpassword123"),
        first_name="Analysis",
        last_name="Musician",
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_performance(db, musician_id: int) -> Performance:
    perf = Performance(
        title="Etude in C Major",
        description="Tempo study",
        audio_file_url="https://example.com/audio/etude-c.mp3",
        musician_id=musician_id,
        status="pending",
    )
    db.add(perf)
    db.commit()
    db.refresh(perf)
    return perf


def test_run_analysis_service_generates_scores():
    db = SessionLocal()
    try:
        musician = _ensure_musician_user(db)
        performance = _create_performance(db, musician.id)

        analysis = AIAnalysisService.run_analysis(db, performance)

        assert analysis.status.value == "completed"
        assert analysis.technique_score is not None
        assert analysis.timing_score is not None
        assert analysis.intonation_score is not None
        assert 60 <= analysis.technique_score <= 100
        assert 60 <= analysis.timing_score <= 100
        assert 60 <= analysis.intonation_score <= 100
        assert analysis.overall_ai_score is not None
    finally:
        db.close()


def test_analyze_performance_endpoint_returns_analysis():
    db = SessionLocal()
    try:
        musician = _ensure_musician_user(db)
        performance = _create_performance(db, musician.id)

        token, _ = create_access_token(
            {
                "sub": musician.id,
                "username": musician.username,
                "role": "musician",
            }
        )

        response = client.post(
            f"/api/v1/performances/{performance.id}/analyze",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["performance_id"] == performance.id
        assert data["status"] in {"pending", "running", "completed"}

        get_response = client.get(
            f"/api/v1/performances/{performance.id}/analysis",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 200
        assert get_response.json()["status"] in {"completed", "pending", "running", "failed"}
    finally:
        db.close()
