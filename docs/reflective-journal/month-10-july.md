# Month 10 Reflective Journal – Feature Sprint and Cloud Deployment Under Pressure

*July 2026 — Final Year Project, Cybersecurity Specialisation*

## The Full DevSecOps Loop, Under Pressure

July was, by a wide margin, the most intense month of the project — nearly two hundred commits, dwarfing every previous month combined. With exams behind me, I threw the reclaimed time at the two biggest remaining pieces of the system: the AI-driven evaluation pipeline and getting the whole thing running somewhere other than my own machine.

On the AI side, I built the audio analysis pipeline using Librosa for similarity scoring against reference tracks, and stood up MinIO locally to test S3-compatible storage before committing to a real cloud provider. That local testing suite — automated tests running against MinIO — gave me the confidence to then implement AWS S3 file storage properly, provisioned through Terraform rather than clicked together manually in a console, which paid off later when I needed to reproduce the same infrastructure for a staging environment.

Security work ran in parallel rather than as an afterthought, which I was pleased about given how central it had been to my planning back in February. I completed rate limiting across every API endpoint, fixed role-normalisation bugs so role values were accepted consistently regardless of case, and added comprehensive error handling and validation to the login and registration forms. I also had to resolve several CI security blockers that CodeQL, Bandit, and gitleaks correctly flagged — a good reminder that a strict pipeline occasionally slows you down precisely when you're in a hurry, which is exactly when it's most valuable.

The hardest part of the month, honestly, was deployment. Getting the backend running on Render exposed a string of environment-parity problems that hadn't shown up in Docker locally: incorrect build context, a misconfigured root directory, port binding issues, proxy headers not being trusted, and a frontend routing setup that didn't behave the same way in production as it did locally. Each fix was small, but the sheer number of them was a real lesson in how much environment configuration, not application logic, ends up driving production incidents. Building a proper staging environment before promoting anything to production turned out to be the single most valuable decision of the month — it caught issues before they reached real users rather than after.

By July 31st, staging had been promoted to production, and the core loop I'd been planning since December — secure design, automated testing, CI enforcement, staged deployment — was finally running end to end. Reflecting on the month as a whole, it felt like the payoff for every earlier month's planning: the architecture from March, the tooling from April, and even the discipline I forced myself to keep during June's slower pace all came together to make an otherwise overwhelming month manageable rather than chaotic.
