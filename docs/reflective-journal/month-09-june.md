# Month 9 Reflective Journal – Maintaining Momentum Under Exam Pressure

*June 2026 — Final Year Project, Cybersecurity Specialisation*

## A Quieter Month, By Necessity

If May was the fastest month of the project so far, June was the slowest — and I want to reflect on that honestly rather than gloss over it. End-of-year exams and coursework deadlines for other modules took up most of my available time, and my commit activity dropped sharply as a result. Where May had produced dozens of commits, June's output was a fraction of that. Coming into a final-year project, I had expected to feel guilty about this kind of slowdown, but treating it as an expected part of Agile Scrum — a lighter sprint rather than a failed one — helped me keep perspective rather than panic.

What I did manage to ship in June was still meaningful, even if smaller in volume. I added an admin user delete action and a corresponding admin user edit UI in the admin panel, along with a dedicated performance submission page for musicians. Small as they sound, these features closed gaps I had noted during May's RBAC work but hadn't had time to build immediately.

One change I'm particularly glad I made this month was refactoring user deactivation to use a confirmation modal rather than an immediate, irreversible action. It was a small usability change, but it directly reflects the secure-design principle I'd been carrying since the February threat-modelling exercise: destructive actions, especially ones affecting another user's account, should require deliberate confirmation rather than a single accidental click. I also committed some backend and frontend environment and configuration updates that had been accumulating, keeping the project's configuration management tidy even though feature output was low.

The main reflection from June is about sprint planning realism. Going into the project, I had implicitly assumed a fairly even pace across the summer months, but June proved that assumption wrong. The useful lesson wasn't to work through exams to protect commit numbers, but to build slack into my sprint planning for exactly this kind of clash, and to make sure that whatever does get shipped in a lighter month is still done with the same security and usability discipline as a busier one — which the deactivation-confirmation change, in particular, gave me confidence I had managed to do.
