# Good First Issues

This page tracks beginner-friendly tasks with clear acceptance criteria.

## How to Use This List

- Pick one issue at a time.
- Comment on the issue before starting to avoid duplicate work.
- Keep PRs focused and small.
- Run `make ci` before opening a PR.

## Starter Tasks

### 1) Add tests for `fetch_missing_pdfs.py` source prioritization

- Goal: verify PDF source fallback order is stable (direct URL -> arXiv -> Unpaywall).
- Scope:
  - add fixture-driven tests in `tests/`
  - cover at least one success and one fallback path
- Acceptance criteria:
  - tests run offline
  - no external API calls in unit tests
  - `make ci` passes

### 2) Add tests for `export_zotero_pdfs_to_local.py` path sanitization

- Goal: ensure invalid filename characters are handled safely across platforms.
- Scope:
  - add unit tests for title-to-filename conversion
  - cover duplicate name collision behavior
- Acceptance criteria:
  - tests include at least three edge-case titles
  - behavior is deterministic
  - `make ci` passes

### 3) Improve docs for common `.env` mistakes

- Goal: reduce first-run setup failures.
- Scope:
  - extend `docs/TROUBLESHOOTING.md` with missing key / wrong provider / invalid path examples
  - include exact command to reproduce and fix
- Acceptance criteria:
  - each new case contains "symptom", "cause", "fix"
  - all markdown links remain valid
  - `make ci` passes

### 4) Add smoke tests for README_EN command snippets

- Goal: keep English docs executable and up to date.
- Scope:
  - extend `tests/test_docs_commands.py`
  - include at least one command from each major section
- Acceptance criteria:
  - tests avoid destructive operations
  - CI validates added commands
  - `make ci` passes

### 5) Improve issue template clarity for reproducibility

- Goal: raise issue quality and reduce maintainer back-and-forth.
- Scope:
  - refine prompts in `.github/ISSUE_TEMPLATE/bug_report.yml`
  - add explicit fields for command, logs, and environment
- Acceptance criteria:
  - template remains concise
  - no broken issue template config
  - `make ci` passes

## Propose a New Starter Task

If you find a task that is self-contained and has clear expected output, open a Feature Request and prefix the title with `[good-first-issue]`.
