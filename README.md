# Musician Evaluation System

Final-year cybersecurity capstone: an AI-driven musician performance evaluation platform with security-by-design.

## What this repo contains
- [backend/](C:/Users/Admin/Documents/Repos/Musician-Eval-System.worktrees/update-status-summary/backend) — FastAPI, PostgreSQL, Celery, Redis
- [frontend/](C:/Users/Admin/Documents/Repos/Musician-Eval-System.worktrees/update-status-summary/frontend) — React + TypeScript + Vite
- [docs/](C:/Users/Admin/Documents/Repos/Musician-Eval-System.worktrees/update-status-summary/docs) — documentation index and guides

## Running the app (step by step)

There are three supported ways to run this app:

### 1) Local development without Docker
Run backend and frontend directly on your machine.

1. Install prerequisites: Python 3.11+, Node.js 20+, PostgreSQL, Redis.
2. Start PostgreSQL and Redis locally.
3. Start backend:
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python -m app.core.init_db
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   - Local uploads are saved to `backend/uploads/` by default, so no S3/Docker storage service is needed for dev.
4. In a second terminal, start frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
5. Open `http://localhost:5173` (frontend). Backend API runs at `http://localhost:8000`.

### 2) Local development with Docker Compose
Run the full stack in containers (PostgreSQL, Redis, backend, frontend).

1. Install Docker Desktop.
2. From repo root, run:
   ```bash
   docker compose up --build
   ```
3. Wait for containers to become healthy.
4. Open `http://localhost:5173`.
5. To stop:
   ```bash
   docker compose down
   ```

### 3) Production deployment on Render
Run as a hosted deployment (not localhost).

1. Push this repo to GitHub (including `render.yaml`).
2. In Render, create a new **Blueprint** from the GitHub repo.
3. Set backend environment secrets in Render for the storage mode you use:
   - local disk uploads are for development only
   - S3-compatible storage needs `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`, `AWS_REGION`
4. Add GitHub Actions secrets:
   - `RENDER_DEPLOY_HOOK_BACKEND`
   - `RENDER_DEPLOY_HOOK_FRONTEND`
5. Push to `main` to trigger CI/CD deploy.
6. Open the Render service URLs for backend/frontend.

## Deployment details (Render)

CI/CD is handled by GitHub Actions:
- **CI** (`ci.yml`) — runs tests, lint, security scans on every push/PR to `main`
- **CD** (`deploy.yml`) — deploys to Render automatically after CI passes on `main`

### One-time Render setup

1. Push this repo to GitHub (including `render.yaml`)
2. Go to [Render Dashboard](https://dashboard.render.com) → **New → Blueprint**
3. Connect your GitHub repo — Render creates all services from `render.yaml`
4. After services are created, copy each service's **Deploy Hook URL**:
   - Render Dashboard → service → **Settings → Deploy Hook**
5. Add these as GitHub repository secrets (**Settings → Secrets → Actions**):
   - `RENDER_DEPLOY_HOOK_BACKEND`
   - `RENDER_DEPLOY_HOOK_FRONTEND`
6. Set sensitive env vars manually in the Render dashboard (never commit these):
   - Backend service → **Environment**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`, `AWS_REGION`

### Deploy flow
```
Push to main
    ↓
GitHub Actions CI (tests · lint · security)
    ↓ passes
GitHub Actions CD → triggers Render Deploy Hooks
    ↓
Render builds & deploys backend + frontend
```

## Docs

See the documentation index: [docs/README.md](C:/Users/Admin/Documents/Repos/Musician-Eval-System.worktrees/update-status-summary/docs/README.md)

## Backend features

The backend includes upload endpoints for audio files:

- `POST /api/v1/performances/upload-audio` (multipart form data: `title`, optional `description`, `audio_file`)

Phase 1 of the core challenge workflow is also in place:

- `POST /api/v1/challenges/reference-tracks`
- `GET /api/v1/challenges/reference-tracks`
- `POST /api/v1/challenges/assignments`
- `GET /api/v1/challenges/assignments`
- `POST /api/v1/challenges/assignments/{assignment_id}/submit`
- `GET /api/v1/challenges/submissions`

For local development without Docker, uploads are stored on disk automatically.

Set these backend environment variables to use S3-compatible storage instead:

- `AWS_REGION`
- `S3_BUCKET_NAME`
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (or use IAM role/default credential chain)
- optional `S3_ENDPOINT_URL` (for LocalStack/custom endpoints)
