# Reflective Journal – Combined (October 2025 – July 2026)

> This file combines all nine monthly reflective journal entries for the project, in chronological order. Month 4 (January 2026) is intentionally omitted per instruction. Individual entries also exist as standalone files in this folder.

---

## Month 1 Reflective Journal – Project Definition and Scoping Phase

*October 2025 — Final Year Project, Cybersecurity Specialisation*

### Context and Project Status

During this month, the primary focus of the project was the exploration, evaluation, and scoping of a suitable final-year project aligned with my cybersecurity specialisation, academic learning outcomes, and personal interests. At this early stage, no definitive project had been selected; instead, emphasis was placed on identifying problem domains that could support both technical depth and professional relevance.

Three potential project directions emerged during this exploratory phase: a musical vocal parts splitter, a spending analyser, and an Intelligent Musician Task Management and Performance Evaluation System using AI-driven audio and video analysis. This phase prioritised research, feasibility assessment, and reflective comparison rather than implementation, which is appropriate at this point in the project lifecycle.

A key influence throughout this process was my long-standing passion for music, including playing musical instruments, arranging songs, and supporting churches and bands in coordinating musicians for services and musical projects. This practical experience informed my interest in developing technology-driven solutions that address real-world organisational and performance challenges within music-based communities, while still meeting the expectations of a cybersecurity-focused final-year project.

### Evaluation of Proposed Project Options

**Musical Vocal Parts Splitter.** This idea aimed to separate vocal components, such as lead vocals and harmonies, from mixed audio tracks, motivated by challenges commonly encountered during rehearsals in church and band environments where musicians often need to practise independently. However, further reflection highlighted limitations from both a feasibility and cybersecurity perspective: the project would rely heavily on advanced machine learning models and audio processing pipelines, potentially reducing the opportunity to demonstrate core cybersecurity competencies, with security considerations largely limited to model integrity and data handling.

**Spending Analyser.** This option focused on analysing financial transaction data to identify spending patterns. From a cybersecurity standpoint, it presented clearer opportunities to explore secure data storage, access control, encryption, and privacy considerations, aligning well with cybersecurity principles. Despite these strengths, it lacked a strong personal or domain-specific motivation, raising concerns about long-term engagement and the potential to demonstrate meaningful domain-driven design decisions.

**Intelligent Musician Task Management and Performance Evaluation System.** This third option emerged as a particularly strong candidate. It would support churches, bands, and music teams by managing musician availability, assigning performance-related tasks, and evaluating musical performance using structured criteria derived from audio and video inputs. It aligns closely with my personal experience in organising musicians and arranging music, while offering substantial scope for cybersecurity-focused system design, since the platform would inherently involve sensitive data — performance recordings, personal profiles, scheduling information, and evaluative feedback — creating a realistic context for secure authentication, role-based access control, data encryption, secure media storage, and protection against unauthorised access or misuse. The integration of AI-driven analysis also introduces additional considerations around model integrity, data provenance, and ethical handling of recorded media.

### Decision-Making Challenges and Constraints

A key challenge during this phase was balancing personal passion, technical ambition, and cybersecurity depth. While the vocal parts splitter aligned strongly with musical interests, its limited security scope posed a risk to sufficient alignment with my chosen specialisation; conversely, the spending analyser offered strong security relevance but lacked domain engagement. The intelligent musician management system addressed this tension by combining a meaningful real-world problem with a technically rich and security-critical architecture. This reflection highlighted an important learning point: a strong final-year project should not only demonstrate technical competence but also reflect context-aware security thinking, where system functionality and protection mechanisms evolve together.

### Learning and Skills Development

This exploratory phase significantly strengthened my project planning, risk assessment, and professional judgement skills. Evaluating multiple project ideas through a cybersecurity lens reinforced the importance of threat modelling, data sensitivity classification, and architectural foresight before implementation begins. Reflecting on my involvement in music-based collaboration also helped clarify how personal experience can inform system requirements while still demanding objective, security-driven evaluation — mirroring real-world cybersecurity practice, where solutions must be tailored to domain-specific risks rather than applied generically.

### Evaluation of Current Progress

Although no development work has commenced, this phase represents meaningful progress. The project direction is now informed by a clearer understanding of how cybersecurity principles can be embedded into system design from the outset. Identifying the intelligent musician management system as a strong option reflects a deliberate and strategic approach to project selection, reducing the likelihood of scope misalignment or insufficient security depth later in the project lifecycle.

### Forward Plan

In the coming month, the focus will be on finalising the project selection through supervisor consultation and refined feasibility analysis. If the intelligent musician task management system is selected, the next steps will include requirements specification, threat modelling, and secure architecture design, with particular attention to authentication, data protection, and ethical handling of audio and video content, ensuring cybersecurity considerations remain central throughout the remainder of the project.

---

## Month 2 Reflective Journal – Requirements Analysis, Threat Modelling, and Secure Architecture Design

*November 2025 — Final Year Project, Cybersecurity Specialisation*

### Context and Project Status

During this month, the project progressed from high-level planning into formal requirements analysis and secure system design. Following the selection of the Intelligent Musician Task Management and Performance Evaluation System, the focus shifted towards translating real-world needs into structured functional and non-functional requirements, with cybersecurity considerations embedded throughout. This phase represents a critical transition point in the project lifecycle, where early design decisions directly influence system security, scalability, and maintainability, so priority was given to architectural clarity and threat awareness rather than early implementation.

### Requirements Analysis and Real-World Context

Requirements were derived from practical scenarios observed within church and band environments, including musician coordination, task assignment, and performance review. These were refined into functional requirements such as role-based task management, controlled access to performance feedback, and secure handling of audio and video recordings. In parallel, non-functional requirements were defined with a strong emphasis on confidentiality, integrity, and accountability, reflecting the sensitivity of personal and performance-related data. This phase required applying knowledge acquired throughout the programme, particularly in secure system design and data protection, to a real-world problem involving multimedia data. The system was intentionally scoped as a medium-to-large scale project, consisting of multiple interacting components, including user management, secure media storage, AI-assisted analysis, and access control layers.

### Threat Modelling and Security-Driven Design

A key outcome of this month was the introduction of structured threat modelling at the design stage. Potential threats were identified informally using a STRIDE-inspired approach, focusing on risks such as unauthorised access to recordings, tampering with performance evaluations, and misuse of privileged roles. This exercise reinforced the importance of identifying attack surfaces early and designing controls proactively rather than reactively — for example, the decision to separate media storage from core application logic was informed by the need to minimise the impact of a potential compromise, reflecting a security-first mindset consistent with professional cybersecurity practice.

### Architecture Design and Technical Decisions

The proposed system architecture adopts a modular design, separating authentication, task management, media handling, and AI-assisted evaluation into distinct components, supporting scalability while enabling fine-grained access control between system functions. Rather than prioritising advanced AI implementation, design decisions focused on how AI features integrate securely into the overall system, ensuring that data provenance, access control, and auditability are maintained — a conscious trade-off between technical ambition and secure, defensible system design. All architectural decisions were documented alongside their security rationale to support later implementation and defence.

### Project Planning and Time Management

From a project management perspective, this month required careful prioritisation to meet upcoming deadlines. Design and security analysis tasks were completed ahead of implementation to reduce rework later in the project lifecycle, and features with higher security risk were deliberately addressed earlier, ensuring foundational components are stable before additional functionality is introduced. This risk-based planning approach reflects a more professional and disciplined method of time management compared to earlier academic projects.

### Communication, Feedback, and Professional Development

Engagement with supervisor feedback during this phase highlighted the importance of clearly communicating technical decisions in a structured and defensible manner. In response, architectural diagrams and written explanations were refined to emphasise *why* security decisions were made, rather than simply *what* was implemented. This process contributed to the development of clearer technical storytelling skills, which are essential when presenting complex cybersecurity concepts to non-specialist stakeholders.

### Evaluation of Progress

By the end of this month, the project had a well-defined requirements set, an initial threat model, and a security-focused architectural design. While no implementation has yet commenced, this stage represents significant progress, as it establishes a robust foundation for secure development and testing in subsequent phases.

### Forward Plan

The next phase will focus on implementing core system components, beginning with authentication, role-based access control, and secure media storage. Security testing considerations will be introduced alongside development to ensure alignment between design intent and implementation behaviour.

---

## Month 3 Reflective Journal – Agile Scrum with DevSecOps

*December 2025 — Final Year Project, Cybersecurity Specialisation*

### Project Commitment and Secure Development Methodology

During Month 3 of my final year project, I made a clear commitment to the Intelligent Musician Task Management and Performance Evaluation System Using AI-Driven Audio and Video Analysis as my chosen project. This decision followed earlier exploration of alternative ideas, including a musical vocal parts splitter and a personal spending analyser. While these options were technically viable, I concluded that the Intelligent Musician System best aligned with both my academic specialisation in cybersecurity and my personal passion for music.

Music has always been a significant part of my life. I actively play musical instruments, arrange songs, and support churches and bands by helping them identify and organise talented musicians for services and musical projects. This background strongly influenced my decision, as the chosen project allows me to address a real-world problem I have personally observed, while also applying advanced technical and security concepts.

With the project scope defined, I selected Agile Scrum as the primary software development methodology, supported by DevSecOps principles. I chose this approach because the project involves evolving requirements, particularly in relation to AI-driven performance analysis and user interaction. Agile Scrum enables me to deliver functionality incrementally, gather feedback early, and adapt the system design as the project progresses.

Given the cybersecurity focus of my degree and the sensitivity of the data involved, I embedded DevSecOps practices into the development lifecycle from the outset. The system processes audio and video recordings of musicians, which introduces privacy, integrity, and access control concerns. To address these risks, I planned security controls such as encrypted data storage and transmission, secure authentication and authorisation mechanisms, strict input validation for media uploads, and detailed logging to support accountability.

I structured the project into short, time-boxed sprints, each with clearly defined objectives, including secure user onboarding, role-based task assignment, and protected media handling. I also introduced a lightweight CI/CD pipeline to support continuous integration. This pipeline includes automated testing, static code analysis, and dependency vulnerability scanning, enabling me to identify defects and security issues early while managing my time more effectively.

Overall, Month 3 represented a transition from idea exploration to structured and secure implementation. By adopting Agile Scrum with DevSecOps, I aligned my project with real-world industry practices while ensuring that cybersecurity considerations remain central to the system's design and development.

---

## Month 5 Reflective Journal – Requirements Engineering and Threat Modelling

*February 2026 — Final Year Project, Cybersecurity Specialisation*

### From Concept to Formal Requirements

Having committed to the Intelligent Musician Task Management and Performance Evaluation System in December and settled on Agile Scrum with DevSecOps as my working methodology, February was the month I turned that commitment into something concrete. I went back to my original problem statement — the difficulty churches, bands, and ensembles have in fairly and consistently assessing musicians against a reference performance — and broke it down into functional user stories for the three roles I had envisaged at the time: administrator, evaluator, and musician. Writing these stories forced me to be honest about scope, and I quickly realised my first draft was too ambitious for a single academic year.

Alongside the functional work, I spent a significant amount of time reading around AI-driven audio comparison techniques, since this sits at the core of the system's value proposition. I looked into spectral similarity measures, MFCC-based comparison, and libraries such as Librosa, which gave me confidence that audio-only analysis was achievable within my timeframe, whereas the video-analysis element I had originally considered was not. Narrowing the MVP to audio comparison was a difficult but necessary decision, and one I recorded clearly in my requirements documentation so the rationale would be visible later in the project.

Because the system processes personal recordings of real musicians, I also reviewed relevant standards early rather than leaving security as an afterthought: OWASP ASVS, the OWASP Top 10, and basic GDPR principles around consent and data minimisation for uploaded audio. This reading directly shaped several non-functional requirements — encrypted storage and transmission, strict role-based access control, audit logging of who accessed or modified evaluation data, and validation of anything a user uploads.

To make those requirements concrete rather than aspirational, I ran a lightweight STRIDE threat-modelling exercise against the core data flows I expected to build: audio upload, evaluation scoring, and credential storage. This surfaced specific risks I hadn't fully considered on paper, such as insecure direct object references on performance recordings and the risk of brute-force login attempts, and gave me a mitigation list — JWT-based authentication, strong password hashing, upload validation, and rate limiting — that I could carry directly into design and, eventually, into the codebase in later months.

Reflecting on the month, I think the biggest lesson was the value of doing this thinking before writing any code. My cybersecurity specialisation naturally pushes me toward secure-by-design thinking, but this was the first time I forced myself to formalise it into requirements and a threat model rather than treating security as something to bolt on afterwards. It also gave me a much clearer, more defensible scope to take into supervisor discussions and into the architecture and design work planned for March.

---

## Month 6 Reflective Journal – System Architecture and Security Design

*March 2026 — Final Year Project, Cybersecurity Specialisation*

### Turning the Threat Model into an Architecture

With requirements and a threat model in place from February, March was about designing a system architecture that could actually satisfy them. I settled on a FastAPI backend with PostgreSQL for persistence, and Celery with Redis to handle audio-scoring work asynchronously so that uploading a performance would never block the user on a long-running comparison job. For the frontend I chose React with TypeScript and Vite, mainly because strong typing across the API boundary reduces a whole category of bugs I did not want to be debugging late in the project. I documented these decisions along with the alternatives I rejected, so the choices would be traceable rather than arbitrary.

A large part of the month went into entity and API design. I sketched an entity-relationship model covering users, reference tracks, performances, and evaluations, and paired it with rough API contracts for authentication, uploads, and scoring endpoints. Designing the RBAC matrix at this stage — deciding exactly what an administrator, evaluator, and musician could and could not do — turned out to be more time-consuming than I expected, but it meant the permission logic was designed deliberately rather than added ad hoc once the API existed.

Security design was woven directly into the architecture rather than treated as a separate document. I planned the authentication flow around short-lived JWT access tokens with a longer-lived refresh token, argon2id for password hashing, and a validation pipeline for uploads that would check file type, size, and content before anything touched storage. I also decided early that Docker would be the standard way to run every environment, so that "it works on my machine" differences couldn't quietly reintroduce vulnerabilities or configuration drift between development and whatever I eventually deployed to.

To keep the DevSecOps commitment from December meaningful rather than aspirational, I designed the CI/CD pipeline itself before writing application code: linting, automated tests, static analysis, and dependency scanning as required checks on every change. Planning this in March meant that when Sprint 0 began, the pipeline could be one of the first things built, rather than something retrofitted once bad habits had already formed.

Looking back, March was the month where the project stopped being a set of documents and started feeling like a system I could actually build. The main lesson was how much easier security is to design in than to add in later — decisions like the RBAC matrix and the upload validation pipeline were far cheaper to get right on paper than they would have been to rework inside a half-built API. That gave me real confidence heading into the final planning month before implementation began.

---

## Month 7 Reflective Journal – Interim Reporting and Sprint 0 Preparation

*April 2026 — Final Year Project, Cybersecurity Specialisation*

### Closing the Planning Phase

April was the bridge between design and implementation. My main deliverable for the month was my interim report, which forced me to write down, in a form someone else could critique, exactly what I had decided in February and March and why. Preparing it was a useful discipline in itself: articulating the threat model, the architecture, and the reasoning behind narrowing scope to audio-only evaluation to a reader outside my own head exposed a few gaps, particularly around how password reset and account recovery should work securely, which I hadn't fully specified before.

With the report submitted, I turned my attention to getting ready to actually build. I finalised the sprint backlog into short, time-boxed sprints with a clear Definition of Done for each, matching the Agile Scrum approach I had committed to back in December. I set up the tooling I knew I would need from day one rather than retrofitting it later: a `pyproject.toml` and dependency files for the backend, ruff and bandit for linting and static security analysis, and a GitHub repository with branch protection enabled so that CI checks would be a genuine gate rather than a formality.

I also spent time provisioning the accounts and services the architecture depended on — a Render account for eventual deployment, an AWS free-tier account for S3 and Terraform experimentation, and draft GitHub Actions workflow templates for CI, security scanning, and CodeQL that I could adapt once real code existed. Sketching an environment strategy across development, test, staging, and production at this stage, rather than improvising it later, meant I wasn't making infrastructure decisions under pressure once deadlines were closer.

April also required a fair amount of honest time-management reflection. Final-year exams and coursework for other modules were competing directly with project time, and I had to accept that some of the polish I wanted to add to the design documentation would have to wait. Rather than fight that, I used the pressure to prioritise: finish the report, finalise the backlog, and get the tooling in place, and treat anything beyond that as a stretch goal.

By the end of the month, the project felt ready to move from planning into Sprint 0. The clearest lesson from April was that the time spent setting up CI/CD, linting, and environment strategy before writing a single line of application code paid for itself almost immediately once implementation started in May — I wasn't discovering pipeline problems and real feature bugs at the same time.

---

## Month 8 Reflective Journal – Sprint 0: Scaffolding the Secure Foundation

*May 2026 — Final Year Project, Cybersecurity Specialisation*

### From Design Documents to Working Code

May was when the project stopped being documentation and became a running system. I opened Sprint 0 with the initial project scaffold, and within the same day had CI, dependency-security, and CodeQL workflows committed alongside it — a direct result of the tooling-first approach I set up in April. Seeing those checks run automatically against my very first commits, rather than being added weeks later, was genuinely satisfying: it meant the DevSecOps discipline I had only planned on paper in December and March was now enforced by the pipeline itself.

The first real engineering push was restructuring the FastAPI backend into a production-ready architecture — clear separation between API routers, core configuration, database access, and services — instead of the flatter layout I'd prototyped with. I also had to fix a batch of ruff linting errors and update dependencies to compatible versions almost immediately, which was a useful early reminder that static analysis and dependency management need constant small attention rather than being a one-off setup task.

The RBAC design from March came to life this month too: I implemented the refresh token endpoint and completed the role-based access control system, giving administrators, evaluators, and musicians the distinct permissions I had modelled earlier. In parallel, I caught myself committing documentation with sensitive example values in it and had to go back and redact them — a small mistake, but a good early lesson in reviewing docs with the same security lens I apply to code.

On the frontend, I built out the React application with authentication and role-based UI, wired it up against the backend through axios, and added a frontend auth smoke test. That smoke test earned its keep almost immediately: it caught an auth serialization mismatch between backend and frontend that would otherwise have been a confusing bug to track down later. Getting Docker Compose working cleanly across backend, frontend, and database rounded out the month, giving me the same environment parity I had planned for back in March.

Looking back, May was intense but rewarding — the fastest-moving month so far, with 36 commits compared to the handful in earlier planning months. The clearest lesson was how much the February–April planning work paid off: I was fixing real implementation bugs like the auth serialization issue, not still arguing with myself about architecture. It also reinforced the value of writing even a minimal smoke test early, since it caught a genuine integration bug before it could compound.

---

## Month 9 Reflective Journal – Maintaining Momentum Under Exam Pressure

*June 2026 — Final Year Project, Cybersecurity Specialisation*

### A Quieter Month, By Necessity

If May was the fastest month of the project so far, June was the slowest — and I want to reflect on that honestly rather than gloss over it. End-of-year exams and coursework deadlines for other modules took up most of my available time, and my commit activity dropped sharply as a result. Where May had produced dozens of commits, June's output was a fraction of that. Coming into a final-year project, I had expected to feel guilty about this kind of slowdown, but treating it as an expected part of Agile Scrum — a lighter sprint rather than a failed one — helped me keep perspective rather than panic.

What I did manage to ship in June was still meaningful, even if smaller in volume. I added an admin user delete action and a corresponding admin user edit UI in the admin panel, along with a dedicated performance submission page for musicians. Small as they sound, these features closed gaps I had noted during May's RBAC work but hadn't had time to build immediately.

One change I'm particularly glad I made this month was refactoring user deactivation to use a confirmation modal rather than an immediate, irreversible action. It was a small usability change, but it directly reflects the secure-design principle I'd been carrying since the February threat-modelling exercise: destructive actions, especially ones affecting another user's account, should require deliberate confirmation rather than a single accidental click. I also committed some backend and frontend environment and configuration updates that had been accumulating, keeping the project's configuration management tidy even though feature output was low.

The main reflection from June is about sprint planning realism. Going into the project, I had implicitly assumed a fairly even pace across the summer months, but June proved that assumption wrong. The useful lesson wasn't to work through exams to protect commit numbers, but to build slack into my sprint planning for exactly this kind of clash, and to make sure that whatever does get shipped in a lighter month is still done with the same security and usability discipline as a busier one — which the deactivation-confirmation change, in particular, gave me confidence I had managed to do.

---

## Month 10 Reflective Journal – Feature Sprint and Cloud Deployment Under Pressure

*July 2026 — Final Year Project, Cybersecurity Specialisation*

### The Full DevSecOps Loop, Under Pressure

July was, by a wide margin, the most intense month of the project — nearly two hundred commits, dwarfing every previous month combined. With exams behind me, I threw the reclaimed time at the two biggest remaining pieces of the system: the AI-driven evaluation pipeline and getting the whole thing running somewhere other than my own machine.

On the AI side, I built the audio analysis pipeline using Librosa for similarity scoring against reference tracks, and stood up MinIO locally to test S3-compatible storage before committing to a real cloud provider. That local testing suite — automated tests running against MinIO — gave me the confidence to then implement AWS S3 file storage properly, provisioned through Terraform rather than clicked together manually in a console, which paid off later when I needed to reproduce the same infrastructure for a staging environment.

Security work ran in parallel rather than as an afterthought, which I was pleased about given how central it had been to my planning back in February. I completed rate limiting across every API endpoint, fixed role-normalisation bugs so role values were accepted consistently regardless of case, and added comprehensive error handling and validation to the login and registration forms. I also had to resolve several CI security blockers that CodeQL, Bandit, and gitleaks correctly flagged — a good reminder that a strict pipeline occasionally slows you down precisely when you're in a hurry, which is exactly when it's most valuable.

The hardest part of the month, honestly, was deployment. Getting the backend running on Render exposed a string of environment-parity problems that hadn't shown up in Docker locally: incorrect build context, a misconfigured root directory, port binding issues, proxy headers not being trusted, and a frontend routing setup that didn't behave the same way in production as it did locally. Each fix was small, but the sheer number of them was a real lesson in how much environment configuration, not application logic, ends up driving production incidents. Building a proper staging environment before promoting anything to production turned out to be the single most valuable decision of the month — it caught issues before they reached real users rather than after.

By July 31st, staging had been promoted to production, and the core loop I'd been planning since December — secure design, automated testing, CI enforcement, staged deployment — was finally running end to end. Reflecting on the month as a whole, it felt like the payoff for every earlier month's planning: the architecture from March, the tooling from April, and even the discipline I forced myself to keep during June's slower pace all came together to make an otherwise overwhelming month manageable rather than chaotic.
