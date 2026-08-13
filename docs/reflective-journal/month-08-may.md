# Month 8 Reflective Journal – Sprint 0: Scaffolding the Secure Foundation

*May 2026 — Final Year Project, Cybersecurity Specialisation*

## From Design Documents to Working Code

May was when the project stopped being documentation and became a running system. I opened Sprint 0 with the initial project scaffold, and within the same day had CI, dependency-security, and CodeQL workflows committed alongside it — a direct result of the tooling-first approach I set up in April. Seeing those checks run automatically against my very first commits, rather than being added weeks later, was genuinely satisfying: it meant the DevSecOps discipline I had only planned on paper in December and March was now enforced by the pipeline itself.

The first real engineering push was restructuring the FastAPI backend into a production-ready architecture — clear separation between API routers, core configuration, database access, and services — instead of the flatter layout I'd prototyped with. I also had to fix a batch of ruff linting errors and update dependencies to compatible versions almost immediately, which was a useful early reminder that static analysis and dependency management need constant small attention rather than being a one-off setup task.

The RBAC design from March came to life this month too: I implemented the refresh token endpoint and completed the role-based access control system, giving administrators, evaluators, and musicians the distinct permissions I had modelled earlier. In parallel, I caught myself committing documentation with sensitive example values in it and had to go back and redact them — a small mistake, but a good early lesson in reviewing docs with the same security lens I apply to code.

On the frontend, I built out the React application with authentication and role-based UI, wired it up against the backend through axios, and added a frontend auth smoke test. That smoke test earned its keep almost immediately: it caught an auth serialization mismatch between backend and frontend that would otherwise have been a confusing bug to track down later. Getting Docker Compose working cleanly across backend, frontend, and database rounded out the month, giving me the same environment parity I had planned for back in March.

Looking back, May was intense but rewarding — the fastest-moving month so far, with 36 commits compared to the handful in earlier planning months. The clearest lesson was how much the February–April planning work paid off: I was fixing real implementation bugs like the auth serialization issue, not still arguing with myself about architecture. It also reinforced the value of writing even a minimal smoke test early, since it caught a genuine integration bug before it could compound.
