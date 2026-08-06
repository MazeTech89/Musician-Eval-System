# Musician Evaluation System

Final-year cybersecurity capstone: an AI-driven musician performance evaluation platform with security-by-design.

## Stack
- Backend: FastAPI · PostgreSQL · Celery · Redis · Librosa
- Frontend: React + TypeScript + Vite
- Infra: Docker · Render · S3-compatible storage
- Security: JWT (HS256) · Argon2id · OWASP ASVS L2

## Quick start
```bash
docker compose up --build
```

This project uses Docker Compose for local development and Docker-based validation.

## Environments

This project is set up around four environments:

### 1. Development
- File: [docker-compose.yml](docker-compose.yml)
- Purpose: local day-to-day development
- Characteristics:
  - local frontend against Dockerized backend/services
  - local upload storage enabled
  - debug enabled
  - ports: frontend `5173`, backend `8000`, postgres `5432`, redis `6379`

Run it with:
```bash
docker compose up --build
```

Stop it with:
```bash
docker compose down
```
(Use `docker compose stop` instead if you want to keep the containers around — e.g. to resume
quickly later — rather than removing them.)

### 2. Test
- File: [docker-compose.test.yml](docker-compose.test.yml)
- Purpose: isolated local test/staging-like validation without clashing with dev
- Characteristics:
  - separate database volume and ports
  - debug disabled
  - separate upload directory
  - ports: frontend `5174`, backend `8001`, postgres `5433`, redis `6380`

Run it with:
```bash
docker compose -f docker-compose.test.yml up --build
```

Stop it with:
```bash
docker compose -f docker-compose.test.yml down
```

### 3. Staging
- File: [render.staging.yaml](render.staging.yaml)
- Purpose: real hosted MVP validation before production promotion
- Characteristics:
  - dedicated `staging` branch deploy target
  - Dockerized backend on Render
  - static frontend on Render
  - managed PostgreSQL and Redis
  - persistent disk on the backend for uploaded audio so the current MVP flow works without S3
  - intended for real browser/user validation of the current assignment-scoring flow

### 4. Production
- File: [render.yaml](render.yaml)
- Purpose: hosted deployment
- Characteristics:
  - Dockerized backend on Render
  - static frontend on Render
  - managed PostgreSQL and Redis
  - local upload storage disabled
  - expected to use S3-compatible object storage for audio files
  - deployed from `main` via Render Blueprint / deploy hooks

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:5173/ and the backend at http://localhost:8000.

### Troubleshooting local runs

- **`Conflict. The container name "/musician_eval_..." is already in use`**: a container from a
  previous run (or a different Compose project/worktree using the same `container_name`) is still
  around. Run `docker compose down` first, or remove the specific container with
  `docker rm -f <container_name>`, then re-run `up --build`.
- **`docker compose up --build <service>` also rebuilds/starts services you didn't name**: this is
  expected — `depends_on` pulls in the dependency chain (e.g. `frontend` depends on `backend`,
  which depends on `postgres`/`redis`). Run `docker compose up --build` with no service name to
  bring up the full stack.
- **Postgres/Redis data persists across restarts**: both the dev and test stacks use named Docker
  volumes (`postgres_data`, `backend_uploads`, etc.), so `docker compose down` does not wipe data —
  add `-v` (`docker compose down -v`) if you need a truly clean database, or see stale-data notes
  below.
- **Stale enum/role data causes `ResponseValidationError`/`LookupError` on endpoints like
  `/api/v1/auth/users`**: the test stack's Postgres volume is long-lived and not reset between runs.
  If a Python enum (e.g. `RoleEnum`) was ever shrunk, old rows referencing a removed value will
  break serialization on read. Fix by clearing the affected rows in the test DB (e.g.
  `docker exec musician_eval_test_db psql -U user -d musician_eval_test -c "DELETE FROM \"user\" WHERE role_id NOT IN (SELECT id FROM role);"`)
  or reset entirely with `docker compose -f docker-compose.test.yml down -v`.

## Deployment

### Staging (Render)

The staging environment is designed to validate the current MVP exactly as it works today:
- backend uploads are stored on a Render persistent disk
- the frontend talks to the staging backend
- the deploy path is driven by the `staging` branch

#### One-time staging setup

1. Push this repo to GitHub, including [render.staging.yaml](render.staging.yaml)
2. In Render, create a **new Blueprint** and point it at `render.staging.yaml`
3. Render will create:
   - `musician-eval-staging-backend`
   - `musician-eval-staging-frontend`
   - `musician-eval-staging-db`
   - `musician-eval-staging-redis`
4. Create/push the `staging` branch

#### Staging deploy flow
```
Push to staging
    ↓
GitHub Actions CI + Docker smoke
    ↓ pass
Render auto-deploys the updated staging branch
    ↓
Render deploys staging backend + frontend
```

### Production (Render)

CI/CD is handled by GitHub Actions:
- **CI** (`ci.yml`) — runs tests, lint, security scans on every push/PR to `main` and `staging`
- **Docker smoke test** (`ci.yml`) — boots the isolated test stack and verifies backend/frontend reachability
- **CD** (`deploy.yml`) — deploys to Render automatically after CI passes on `main`

#### One-time production setup

1. Push this repo to GitHub (including `render.yaml`)
2. Go to [Render Dashboard](https://dashboard.render.com) → **New → Blueprint**
3. Connect your GitHub repo — Render creates all services from `render.yaml`
4. After services are created, copy each service's **Deploy Hook URL**:
   - Render Dashboard → service → **Settings → Deploy Hook**
5. Add these as GitHub repository secrets (**Settings → Secrets → Actions**):
   - `RENDER_DEPLOY_HOOK_BACKEND`
   - `RENDER_DEPLOY_HOOK_FRONTEND`
6. Optional: set S3 env vars in the Render dashboard to use object storage for audio uploads. If they are not present, the backend automatically falls back to local disk storage for the current MVP flow.
   - Backend service → **Environment**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`, `AWS_REGION`

#### Production deploy flow
```
Push to main
    ↓
GitHub Actions CI (tests · lint · security)
    ↓ passes
GitHub Actions CD → triggers Render Deploy Hooks
    ↓
Render builds & deploys backend + frontend
```

---

## S3 audio uploads (backend)

The backend now includes a minimal S3 upload endpoint:

- `POST /api/v1/performances/upload-audio` (multipart form data: `title`, optional `description`, `audio_file`)

Set these backend environment variables to enable object-store uploads:

- `AWS_REGION`
- `S3_BUCKET_NAME`
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (or use IAM role/default credential chain)
- optional `S3_ENDPOINT_URL` (for LocalStack/custom endpoints)

If these values are not provided, the backend automatically falls back to local disk storage so the MVP flow still works.
