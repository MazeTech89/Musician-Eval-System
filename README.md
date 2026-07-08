# Musician Evaluation System

Final-year cybersecurity capstone: an AI-driven musician performance evaluation platform with security-by-design.

## Overview

This repository contains a FastAPI backend and a React + TypeScript frontend for evaluating musician performances with authentication, role-based access control, and AI-assisted analysis.

## Prerequisites

- Docker and Docker Compose for the full stack
- Python 3.11+ for local backend runs
- Node.js 18+ for local frontend runs

## Tech Stack
- Backend: FastAPI, SQLAlchemy, PostgreSQL, Pydantic, Python-Jose, Argon2id, Celery, Redis, Librosa
- Frontend: React, TypeScript, Vite, Tailwind CSS, React Router, Axios, Lucide React
- Testing: Pytest, Playwright, FastAPI TestClient
- Infrastructure: Docker Compose, PostgreSQL, Redis
- Security: JWT access/refresh, role-based access control, Argon2 password hashing, OWASP-aligned patterns

## Frontend Features

- User authentication with login and registration
- Role-based dashboard access
- Protected routes
- Responsive UI styled with Tailwind CSS
- Backend API integration through Axios
- Playwright UI smoke testing

## Frontend Scripts

- `npm install` - Install frontend dependencies
- `npm run dev` - Start the Vite development server
- `npm run build` - Build the frontend for production
- `npm run preview` - Preview the production build
- `npm run lint` - Run ESLint
- `npm run test:smoke` - Run the Playwright UI smoke test

## Progress
- ✅ Backend auth flow fixed and validated: registration, login, JWT access token, refresh token, `/auth/me`
- ✅ Backend role serialization and `UserResponse` response handling corrected
- ✅ Backend auth unit tests passed: `24 passed`
- ✅ Frontend auth flow validated: register, login, logout, protected routes
- ✅ Frontend build successful and UI smoke test added with Playwright
- ✅ Browser-based interactive validation completed in VS Code
- ✅ Documentation updated with current setup, progress, and test coverage

## Quick start
Run the full system from the repository root with Docker Compose:

```bash
docker compose up --build
```

Open these URLs after startup:
- Frontend: http://localhost:5173/
- Backend API: http://localhost:8000/

Docker Compose starts PostgreSQL, Redis, the backend, and the frontend together.

## First run checklist

1. Install Docker Desktop.
2. Run `docker compose up --build` from the repository root.
3. Open the frontend at http://localhost:5173/.
4. Use the backend API at http://localhost:8000/.
5. Stop everything with `docker compose down` when you are done.

## Run locally without Docker

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend scripts:

```bash
npm run build
npm run lint
npm run test:smoke
```

The frontend expects the backend API at `http://localhost:8000`, and the Vite dev server proxies API calls during local development.

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

If you are not using Docker Compose for PostgreSQL and Redis, update the backend environment variables before starting the app.

## Project Structure

```text
backend/        FastAPI application, database models, services, tests
frontend/       React application, pages, components, Playwright smoke tests
docker-compose.yml  Local development stack for backend, frontend, PostgreSQL, and Redis
```

## Notes

- The backend container is configured with development settings in `docker-compose.yml`.
- Stop the stack with `docker compose down` when you are done.

## Next Steps

See [PUBLIC_LAUNCH_ROADMAP.md](PUBLIC_LAUNCH_ROADMAP.md) for the recommended path to make this project ready for public end users.

## Troubleshooting

- If Docker Compose fails to start, make sure Docker Desktop is running and try `docker compose down` followed by `docker compose up --build` again.
- If port `5173` or `8000` is already in use, stop the conflicting process or change the exposed ports in `docker-compose.yml`.
- If PowerShell blocks backend activation, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` in an elevated terminal, then activate `.venv\Scripts\Activate.ps1` again.
- If the backend cannot connect to PostgreSQL or Redis outside Docker, confirm those services are running and that the environment variables match your local setup.
