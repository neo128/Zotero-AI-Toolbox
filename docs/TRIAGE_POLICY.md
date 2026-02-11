# Issue Triage Policy

This policy defines response targets and issue lifecycle rules for PaperPilot.

## Response SLA

- First maintainer response: within 3 business days.
- Security reports: acknowledged within 24 hours (private channel via `SECURITY.md`).
- Reproducible regressions: prioritized for the next patch release.

## Required Issue Quality

To be triaged quickly, issues should include:

- exact command(s)
- relevant logs or traceback
- Python version and operating system
- related `.env` profile or key config notes

Issues missing core reproduction info may be labeled `needs-info`.

## Label-Based Workflow

- `bug`: confirmed incorrect behavior.
- `feature`: new capability request.
- `question`: usage/setup support request.
- `good first issue`: beginner-friendly and scoped.
- `needs-info`: blocked on missing reproduction details.
- `blocked`: cannot proceed due to external dependency.
- `duplicate`: covered by an existing issue.

## Lifecycle Rules

- `needs-info`: if no response for 14 days, issue may be closed.
- `question`: if answered and inactive for 7 days, issue may be closed.
- `duplicate`: closed after linking canonical issue.
- `bug`/`feature`: stays open until fixed or explicitly declined with rationale.

## Pull Request Triage

- Initial PR review target: within 5 business days.
- PRs touching CLI behavior should include before/after examples or tests.
- PRs with failing CI are not merged until checks pass.

## Escalation

For urgent breakages affecting core workflows (`watch`, `dedupe`, `summarize`, `sync`):

- open a Bug Report with reproduction steps
- include `regression` in title
- link to the last known good version if available
