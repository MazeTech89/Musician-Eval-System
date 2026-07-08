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