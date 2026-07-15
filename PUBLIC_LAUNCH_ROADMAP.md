# Public Launch Roadmap

This project already has the core product loop in place: user authentication, role-based access control, musician performance submission, evaluator scoring, admin user management, and a baseline AI analysis pipeline.

For a public launch, the work should be split into three phases.

## Phase 1: Public Beta Readiness

Goal: make the current MVP safe and usable for external users.

- Replace the audio URL field with real file upload support and store files in object storage.
- Move secrets, database credentials, and token keys out of source-controlled defaults.
- Use managed PostgreSQL and Redis in production.
- Add HTTPS, a custom domain, and environment-specific configuration.
- Add rate limiting, request logging, and error monitoring.
- Remove or finish placeholder UI items such as the dashboard “Coming soon” sections.
- Add public-facing terms, privacy policy, and support contact information.

## Phase 2: Product Completion

Goal: make the platform feel finished for end users.

- Build evaluation history and reporting pages.
- Add notifications for submissions, evaluations, and admin actions.
- Improve the admin panel with search, filtering, and audit visibility.
- Replace the deterministic AI baseline with a real analysis pipeline or clearly label it as a baseline scoring system.
- Add download/export options for reports if they are part of the product scope.

## Phase 3: Operational Hardening

Goal: make the system supportable at scale.

- Add centralized logs, metrics, and alerting.
- Define backup and restore procedures for the database and uploaded media.
- Add automated smoke tests for the public user journey.
- Create a deployment pipeline for staging and production.
- Add abuse prevention controls such as account lockout, throttling, and upload validation.

## Recommended Order

1. Implement real upload storage.
2. Remove production secrets from defaults.
3. Stand up managed infrastructure.
4. Finish the missing UI surfaces.
5. Add observability and release automation.

## What Is Already Good

- Auth and JWT refresh flow are implemented.
- RBAC is already in place.
- The core pages for dashboard, performances, evaluations, profile, and admin exist.
- Backend and frontend test coverage already exists for key flows.

## Launch Gate

Do not call this production-ready until:

- Users can register, log in, submit performances, and receive evaluations without manual intervention.
- Audio is stored securely and reliably.
- Production secrets are externalized.
- Basic monitoring and error reporting are enabled.
- The public routes are smoke-tested after deployment.

## Current Snapshot (2026-07-15)

Based on current branch state (`auth-ui-backend-fix`) and recent implementation work.

### Completed

- Backend S3 upload flow and object metadata persistence are implemented.
- Infrastructure-as-code for AWS core services (RDS, Redis, ECS, S3, secrets) exists.
- Auth flow hardening and role normalization fixes are in place.
- API rate limiting has been implemented across endpoints.

### In Progress

- Frontend navigation/layout unification is underway (shared navigation component and page refactor).
- Registration success UX has been added and is being integrated into the updated route structure.

### Not Yet Complete (Launch blockers)

- Performance submission UI still relies on an audio URL input instead of direct file upload.
- Dashboard still contains "Coming soon" placeholders.
- Public legal/support pages (Terms, Privacy, Support) are not yet present.
- End-to-end smoke coverage is currently limited to login/register.

## Strict Launch Checklist

Status legend: `[ ]` not started, `[/]` in progress, `[x]` done.

### P0: Must Complete Before Public Launch

- [ ] **FE-Upload-01** Replace performance audio URL field with direct file upload in frontend and call upload endpoint.
	Owner: Frontend Engineer
	Dependency: Existing backend upload endpoint
	Done when: User can submit a file from UI and uploaded object key is stored/retrievable.

- [ ] **QA-E2E-01** Add public-path smoke flow covering register -> login -> create performance -> upload audio -> evaluator view.
	Owner: QA Engineer
	Dependency: FE-Upload-01
	Done when: CI and local run pass with deterministic assertions.

- [ ] **SEC-Secrets-01** Move production secrets out of repository defaults and document secret injection path.
	Owner: DevOps Engineer
	Dependency: None
	Done when: No production secret values in tracked files, deployment uses env/secret manager.

- [ ] **OPS-Obs-01** Enable baseline monitoring: request logs, error tracking, and health alerting.
	Owner: DevOps Engineer
	Dependency: Deployment environment available
	Done when: Error and uptime signals visible in one operational dashboard.

- [ ] **LEGAL-Public-01** Publish Terms, Privacy, and Support pages/routes and expose links from auth/public surfaces.
	Owner: Product/Frontend Engineer
	Dependency: Copy approved
	Done when: Pages are reachable in app and links are visible pre-login.

- [ ] **UX-Dashboard-01** Remove or implement all "Coming soon" sections on dashboard.
	Owner: Frontend Engineer
	Dependency: Product decision per section
	Done when: No placeholder-only cards remain in production UI.

### P1: Should Complete In First Post-Launch Sprint

- [ ] **ADMIN-01** Add admin search/filter/audit visibility improvements.
	Owner: Frontend + Backend Engineers

- [ ] **REPORT-01** Build evaluation history/reporting and optional export path.
	Owner: Product + Frontend + Backend Engineers

- [ ] **NOTIFY-01** Add system notifications for submissions/evaluations/admin actions.
	Owner: Backend Engineer

## Owner Assignment Matrix

- **Frontend Engineer**: FE-Upload-01, UX-Dashboard-01, legal page integration.
- **Backend Engineer**: Support upload contract validation, notification/report APIs as needed.
- **DevOps Engineer**: SEC-Secrets-01, OPS-Obs-01, deploy/runtime configuration checks.
- **QA Engineer**: QA-E2E-01, release candidate verification, launch gate evidence.
- **Product/PM**: Legal copy approval, final launch-go/no-go sign-off.

## One-Week Execution Order (Recommended)

### Day 1 (Mon) - Foundations

1. Lock scope for P0 tasks and owners.
2. Complete secrets externalization plan and environment variable audit.
3. Finalize frontend contract for file upload UX.

### Day 2 (Tue) - Core Build

1. Implement frontend direct file upload flow.
2. Wire upload success/failure states and validation messages.
3. Begin dashboard placeholder removal.

### Day 3 (Wed) - Public Surface

1. Ship Terms, Privacy, and Support pages/routes.
2. Add route links in login/register/public areas.
3. Finish dashboard placeholder cleanup.

### Day 4 (Thu) - Reliability

1. Add end-to-end smoke test for the full public path.
2. Enable error monitoring and request logging in deployment target.
3. Add/verify health checks and alert thresholds.

### Day 5 (Fri) - Release Candidate

1. Run full regression (unit + integration + smoke).
2. Fix blockers only; defer non-blockers to post-launch sprint.
3. Produce launch evidence checklist (test output, monitoring screenshots, secret audit).

### Day 6 (Sat) - Dry Run

1. Staging deployment dry run.
2. Execute smoke suite against staging.
3. Confirm rollback and backup/restore procedure.

### Day 7 (Sun) - Go/No-Go

1. Run launch gate checklist review.
2. PM + Engineering sign-off.
3. Launch or hold based on objective gate status.

## Go/No-Go Checklist (Final)

- [ ] Registration, login, performance submission, and evaluation path works end-to-end.
- [ ] Audio file upload works from UI and stores safely in object storage.
- [ ] Production secrets are externalized and verified.
- [ ] Monitoring and alerting are operational.
- [ ] Public legal/support pages are live.
- [ ] Smoke tests pass in staging immediately before launch.