# Month 2 Reflective Journal – Requirements Analysis, Threat Modelling, and Secure Architecture Design

*November 2025 — Final Year Project, Cybersecurity Specialisation*

## Context and Project Status

During this month, the project progressed from high-level planning into formal requirements analysis and secure system design. Following the selection of the Intelligent Musician Task Management and Performance Evaluation System, the focus shifted towards translating real-world needs into structured functional and non-functional requirements, with cybersecurity considerations embedded throughout.

This phase represents a critical transition point in the project lifecycle, where early design decisions directly influence system security, scalability, and maintainability. As a result, priority was given to architectural clarity and threat awareness rather than early implementation.

## Requirements Analysis and Real-World Context

Requirements were derived from practical scenarios observed within church and band environments, including musician coordination, task assignment, and performance review. These were refined into functional requirements such as role-based task management, controlled access to performance feedback, and secure handling of audio and video recordings.

In parallel, non-functional requirements were defined with a strong emphasis on confidentiality, integrity, and accountability, reflecting the sensitivity of personal and performance-related data. This phase required the application of knowledge acquired throughout the programme, particularly in secure system design and data protection, to a real-world problem involving multimedia data.

The system was intentionally scoped as a medium-to-large scale project, consisting of multiple interacting components, including user management, secure media storage, AI-assisted analysis, and access control layers.

## Threat Modelling and Security-Driven Design

A key outcome of this month was the introduction of structured threat modelling at the design stage. Potential threats were identified informally using a STRIDE-inspired approach, focusing on risks such as unauthorised access to recordings, tampering with performance evaluations, and misuse of privileged roles.

This exercise reinforced the importance of identifying attack surfaces early and designing controls proactively rather than reactively. For example, the decision to separate media storage from core application logic was informed by the need to minimise the impact of a potential compromise. This reflects a security-first mindset consistent with professional cybersecurity practice.

## Architecture Design and Technical Decisions

The proposed system architecture adopts a modular design, separating authentication, task management, media handling, and AI-assisted evaluation into distinct components. This approach supports scalability while enabling fine-grained access control between system functions.

Rather than prioritising advanced AI implementation, design decisions focused on how AI features integrate securely into the overall system, ensuring that data provenance, access control, and auditability are maintained. This reflects a conscious trade-off between technical ambition and secure, defensible system design.

All architectural decisions were documented alongside their security rationale to support later implementation and defence.

## Project Planning and Time Management

From a project management perspective, this month required careful prioritisation to meet upcoming deadlines. Design and security analysis tasks were completed ahead of implementation to reduce rework later in the project lifecycle. Features with higher security risk were deliberately addressed earlier, ensuring that foundational components are stable before additional functionality is introduced.

This risk-based planning approach reflects a more professional and disciplined method of time management compared to earlier academic projects.

## Communication, Feedback, and Professional Development

Engagement with supervisor feedback during this phase highlighted the importance of clearly communicating technical decisions in a structured and defensible manner. In response, architectural diagrams and written explanations were refined to emphasise why security decisions were made, rather than simply what was implemented.

This process contributed to the development of clearer technical storytelling skills, which are essential when presenting complex cybersecurity concepts to non-specialist stakeholders.

## Evaluation of Progress

By the end of this month, the project had a well-defined requirements set, an initial threat model, and a security-focused architectural design. While no implementation has yet commenced, this stage represents significant progress, as it establishes a robust foundation for secure development and testing in subsequent phases.

## Forward Plan

The next phase will focus on implementing core system components, beginning with authentication, role-based access control, and secure media storage. Security testing considerations will be introduced alongside development to ensure alignment between design intent and implementation behaviour.
