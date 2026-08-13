# Month 6 Reflective Journal – System Architecture and Security Design

*March 2026 — Final Year Project, Cybersecurity Specialisation*

## Turning the Threat Model into an Architecture

With requirements and a threat model in place from February, March was about designing a system architecture that could actually satisfy them. I settled on a FastAPI backend with PostgreSQL for persistence, and Celery with Redis to handle audio-scoring work asynchronously so that uploading a performance would never block the user on a long-running comparison job. For the frontend I chose React with TypeScript and Vite, mainly because strong typing across the API boundary reduces a whole category of bugs I did not want to be debugging late in the project. I documented these decisions along with the alternatives I rejected, so the choices would be traceable rather than arbitrary.

A large part of the month went into entity and API design. I sketched an entity-relationship model covering users, reference tracks, performances, and evaluations, and paired it with rough API contracts for authentication, uploads, and scoring endpoints. Designing the RBAC matrix at this stage — deciding exactly what an administrator, evaluator, and musician could and could not do — turned out to be more time-consuming than I expected, but it meant the permission logic was designed deliberately rather than added ad hoc once the API existed.

Security design was woven directly into the architecture rather than treated as a separate document. I planned the authentication flow around short-lived JWT access tokens with a longer-lived refresh token, argon2id for password hashing, and a validation pipeline for uploads that would check file type, size, and content before anything touched storage. I also decided early that Docker would be the standard way to run every environment, so that "it works on my machine" differences couldn't quietly reintroduce vulnerabilities or configuration drift between development and whatever I eventually deployed to.

To keep the DevSecOps commitment from December meaningful rather than aspirational, I designed the CI/CD pipeline itself before writing application code: linting, automated tests, static analysis, and dependency scanning as required checks on every change. Planning this in March meant that when Sprint 0 began, the pipeline could be one of the first things built, rather than something retrofitted once bad habits had already formed.

Looking back, March was the month where the project stopped being a set of documents and started feeling like a system I could actually build. The main lesson was how much easier security is to design in than to add in later — decisions like the RBAC matrix and the upload validation pipeline were far cheaper to get right on paper than they would have been to rework inside a half-built API. That gave me real confidence heading into the final planning month before implementation began.
