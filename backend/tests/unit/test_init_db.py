"""Regression tests for database initialization."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_init_db_imports_reference_models() -> None:
    """The init_db module must register assignment tables before create_all runs."""
    backend_root = Path(__file__).resolve().parents[2]
    script = """
from app.models.user import Base
import app.core.init_db  # noqa: F401

tables = set(Base.metadata.tables)
required = {"assignments", "reference_tracks"}
missing = sorted(required - tables)
if missing:
    raise SystemExit(f"Missing tables in metadata: {missing}")
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=backend_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
