# Backend

This README is backend-only. For the full project guide, see the root [README.md](C:/Users/Admin/Documents/Repos/Musician-Eval-System.worktrees/update-status-summary/README.md).

## What it is

FastAPI backend for the Musician Evaluation System.

## Run locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.core.init_db
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You also need PostgreSQL and Redis available locally.

By default, local uploads are written to `backend/uploads/`, so you can run the app end-to-end without S3 or Docker.

## Docker

The backend is also started by the root `docker compose up --build` command.

## Tests

```bash
cd backend
pytest
```

## Related docs

- [RBAC Implementation Guide](C:/Users/Admin/Documents/Repos/Musician-Eval-System.worktrees/update-status-summary/backend/RBAC_IMPLEMENTATION.md)

## Phase 1 challenge workflow

Backend routes now support the first step of the core challenge flow:

- admin reference-track upload
- assignment creation from a reference track
- musician submission upload against an assignment
- submission listing for review

If you want S3-compatible storage instead of local disk, set the AWS/S3 variables in `backend/.env`.
