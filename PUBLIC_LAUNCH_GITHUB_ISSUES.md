# Public Launch GitHub Issues Pack

Use each block below as a copy-paste issue body in GitHub.
Recommended labels: `launch`, `p0` or `p1`, plus area labels (`frontend`, `backend`, `devops`, `qa`, `product`).

## 1) FE-Upload-01 - Frontend direct audio file upload

Title: [P0][Frontend] FE-Upload-01 Replace Audio URL with direct file upload

Labels: launch, p0, frontend
Assignee: Frontend Engineer
Depends on: Existing backend upload endpoint

Body:

Problem
- Performance submission UI currently uses an audio URL field.

Goal
- Replace URL-based submission with direct file upload in the frontend.

Scope
- Add file input to performance form.
- Call backend upload endpoint after performance create.
- Show upload progress, success, and failure states.
- Validate allowed file types and size before upload.

Acceptance Criteria
- User can create performance and upload audio directly from UI.
- Successful upload persists object key and related metadata.
- Clear validation errors for unsupported type or oversized file.
- Retry path exists for transient upload failures.

Definition of Done
- Manual happy path verified.
- Unit/integration tests added or updated.
- No regression in performance creation flow.

## 2) QA-E2E-01 - Public path smoke E2E

Title: [P0][QA] QA-E2E-01 Add public-path smoke flow (register -> upload -> evaluator view)

Labels: launch, p0, qa, e2e
Assignee: QA Engineer
Depends on: FE-Upload-01

Body:

Problem
- Smoke coverage is currently limited and does not cover the full public journey.

Goal
- Add deterministic E2E smoke test for critical public launch path.

Scope
- Register user.
- Login.
- Create performance.
- Upload audio.
- Verify evaluator can view resulting performance/evaluation surface.

Acceptance Criteria
- Test passes locally and in CI.
- Assertions are deterministic and not timing-flaky.
- Failure output is actionable.

Definition of Done
- Test added to smoke suite.
- CI job updated to run this scenario.
- Test docs updated.

## 3) SEC-Secrets-01 - Secrets externalization

Title: [P0][DevOps] SEC-Secrets-01 Externalize production secrets and document injection path

Labels: launch, p0, devops, security
Assignee: DevOps Engineer
Depends on: None

Body:

Problem
- Production-sensitive values risk living in tracked defaults.

Goal
- Ensure production secrets are not stored in repository defaults.

Scope
- Audit tracked configuration files.
- Remove/replace production values with placeholders.
- Define secret manager and runtime injection path.
- Document required env vars and rotation expectations.

Acceptance Criteria
- No production secret values in tracked repository files.
- Deployment reads secrets from approved secret store/runtime env.
- Team can follow documented setup without ambiguity.

Definition of Done
- Security review completed.
- Secret audit evidence captured.
- Deployment validation passed.

## 4) OPS-Obs-01 - Baseline monitoring and alerting

Title: [P0][DevOps] OPS-Obs-01 Enable baseline logs, error tracking, and health alerts

Labels: launch, p0, devops, observability
Assignee: DevOps Engineer
Depends on: Deployment environment available

Body:

Problem
- Launch requires minimum operational visibility and alerting.

Goal
- Provide production baseline observability for supportability.

Scope
- Centralize request logs.
- Enable error tracking.
- Add health/uptime alerts with thresholds.
- Define incident notification channel.

Acceptance Criteria
- Logs searchable in one place.
- Error events visible with stack/context.
- Health alerts trigger to configured channel.
- Runbook for triage path exists.

Definition of Done
- Dashboard URL shared with team.
- Alert test fired and verified.
- Basic on-call instructions documented.

## 5) LEGAL-Public-01 - Terms, Privacy, Support pages

Title: [P0][Product/Frontend] LEGAL-Public-01 Publish Terms, Privacy, and Support pages

Labels: launch, p0, frontend, product, legal
Assignee: Product/Frontend Engineer
Depends on: Legal copy approved

Body:

Problem
- Public legal/support pages are required for launch readiness.

Goal
- Publish Terms, Privacy, and Support pages and expose links on public/auth surfaces.

Scope
- Add routes and page content for Terms, Privacy, Support.
- Link pages from login/register and other public entry points.
- Ensure mobile and desktop readability.

Acceptance Criteria
- All three pages are reachable without authentication.
- Links are visible on public/auth pages.
- Content is versioned and reviewable.

Definition of Done
- Product/legal sign-off complete.
- Routes covered by smoke checks.

## 6) UX-Dashboard-01 - Remove placeholders

Title: [P0][Frontend] UX-Dashboard-01 Remove or implement all dashboard "Coming soon" placeholders

Labels: launch, p0, frontend, ux
Assignee: Frontend Engineer
Depends on: Product decision per placeholder section

Body:

Problem
- Placeholder-only dashboard sections reduce launch quality.

Goal
- Replace placeholders with real content or remove the sections.

Scope
- Audit all dashboard placeholders.
- Implement minimal launch-ready content or remove cards.
- Keep consistent visual layout and responsive behavior.

Acceptance Criteria
- No placeholder-only sections remain.
- Dashboard remains functional for all roles.
- No broken links/actions introduced.

Definition of Done
- Product review approved.
- UI regression checks pass.

## 7) ADMIN-01 - Admin search/filter/audit visibility

Title: [P1][Admin] ADMIN-01 Improve admin panel search, filtering, and audit visibility

Labels: launch, p1, frontend, backend, admin
Assignee: Frontend + Backend Engineers
Depends on: None

Body:

Problem
- Admin workflows lack efficient discovery/filtering and audit context.

Goal
- Improve manageability in admin panel for post-launch sprint.

Scope
- Add search/filter controls.
- Expose key audit metadata in list/detail views.
- Improve table/list performance for moderate data sizes.

Acceptance Criteria
- Admin can quickly find users/items via search/filter.
- Relevant audit fields are visible and understandable.
- No authorization regression in admin routes.

Definition of Done
- Feature demo complete.
- Tests added for new query/filter behavior.

## 8) REPORT-01 - Evaluation history and reporting

Title: [P1][Reporting] REPORT-01 Build evaluation history/reporting and optional export

Labels: launch, p1, frontend, backend, reporting
Assignee: Product + Frontend + Backend Engineers
Depends on: None

Body:

Problem
- End users need clear historical evaluation visibility after launch.

Goal
- Provide evaluation history/reporting surface and optional export support.

Scope
- Add history views with key filters.
- Provide report details and summary metrics.
- Add export path if approved in scope.

Acceptance Criteria
- Users can access evaluation history without manual support.
- Report pages load with expected filters/sorting.
- Export works if enabled in final scope.

Definition of Done
- Product acceptance completed.
- Test coverage added for primary report paths.

## 9) NOTIFY-01 - Notifications

Title: [P1][Backend] NOTIFY-01 Add notifications for submissions, evaluations, and admin actions

Labels: launch, p1, backend, notifications
Assignee: Backend Engineer
Depends on: None

Body:

Problem
- Users/admins currently lack systematic event notifications.

Goal
- Add notification events for major system actions.

Scope
- Submission created notification.
- Evaluation completed notification.
- Admin action notification for critical changes.
- Minimal delivery mechanism for first release scope.

Acceptance Criteria
- Events emit notifications for the defined actions.
- Delivery failures are logged and observable.
- Notification content is clear and role-appropriate.

Definition of Done
- Event triggers validated in test/staging.
- Monitoring includes notification failure signal.

## Optional Meta Issue - Public Launch Tracker

Title: [Launch Tracker] Public Launch P0/P1 execution board

Labels: launch, tracking
Assignee: PM

Body:

Purpose
- Track progress and dependencies across P0/P1 launch issues.

Checklist
- [ ] FE-Upload-01
- [ ] QA-E2E-01
- [ ] SEC-Secrets-01
- [ ] OPS-Obs-01
- [ ] LEGAL-Public-01
- [ ] UX-Dashboard-01
- [ ] ADMIN-01
- [ ] REPORT-01
- [ ] NOTIFY-01

Exit Criteria
- All P0 items completed.
- Go/No-Go checklist passed in staging.
