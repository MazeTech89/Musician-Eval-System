# Month 7 Reflective Journal – Interim Reporting and Sprint 0 Preparation

*April 2026 — Final Year Project, Cybersecurity Specialisation*

## Closing the Planning Phase

April was the bridge between design and implementation. My main deliverable for the month was my interim report, which forced me to write down, in a form someone else could critique, exactly what I had decided in February and March and why. Preparing it was a useful discipline in itself: articulating the threat model, the architecture, and the reasoning behind narrowing scope to audio-only evaluation to a reader outside my own head exposed a few gaps, particularly around how password reset and account recovery should work securely, which I hadn't fully specified before.

With the report submitted, I turned my attention to getting ready to actually build. I finalised the sprint backlog into short, time-boxed sprints with a clear Definition of Done for each, matching the Agile Scrum approach I had committed to back in December. I set up the tooling I knew I would need from day one rather than retrofitting it later: a `pyproject.toml` and dependency files for the backend, ruff and bandit for linting and static security analysis, and a GitHub repository with branch protection enabled so that CI checks would be a genuine gate rather than a formality.

I also spent time provisioning the accounts and services the architecture depended on — a Render account for eventual deployment, an AWS free-tier account for S3 and Terraform experimentation, and draft GitHub Actions workflow templates for CI, security scanning, and CodeQL that I could adapt once real code existed. Sketching an environment strategy across development, test, staging, and production at this stage, rather than improvising it later, meant I wasn't making infrastructure decisions under pressure once deadlines were closer.

April also required a fair amount of honest time-management reflection. Final-year exams and coursework for other modules were competing directly with project time, and I had to accept that some of the polish I wanted to add to the design documentation would have to wait. Rather than fight that, I used the pressure to prioritise: finish the report, finalise the backlog, and get the tooling in place, and treat anything beyond that as a stretch goal.

By the end of the month, the project felt ready to move from planning into Sprint 0. The clearest lesson from April was that the time spent setting up CI/CD, linting, and environment strategy before writing a single line of application code paid for itself almost immediately once implementation started in May — I wasn't discovering pipeline problems and real feature bugs at the same time.
