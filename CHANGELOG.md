# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added
- GitHub community health files: license, contributing guide, code of conduct, security policy.
- Issue and pull request templates under `.github/`.
- CI workflow with syntax checks, CLI smoke checks, and unit tests.
- Release workflow to publish GitHub Releases on `v*` tags.
- Conversion-first README sections (badges, quick start, example output, roadmap).
- `Makefile` for local developer commands (`install`, `check`, `test`, `ci`).
- `CITATION.cff` for scholarly citation support.
- `ROADMAP.md` and `docs/USE_CASES.md` for direction and practical onboarding.
- Dependabot and CODEOWNERS configuration under `.github/`.
- Environment profile templates:
  - `.env.zotero.example`
  - `.env.zotero_notion.example`
- Troubleshooting and docs quality checks:
  - `docs/TROUBLESHOOTING.md`
  - `tests/test_env_templates.py`
  - `tests/test_markdown_links.py`
- Before/after benchmark examples:
  - `docs/BEFORE_AFTER.md`

### Changed
- Setup instructions now use `pip install -r requirements.txt` for consistency.
- `.gitignore` expanded to ignore generated runtime artifacts and local datasets.

## [0.1.0] - 2026-02-09

### Added
- Initial public baseline for PaperPilot automation scripts.
- End-to-end CLI pipeline around Zotero ingestion, dedupe, summarization, and sync.

[Unreleased]: https://github.com/neo128/PaperPilot/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/neo128/PaperPilot/releases/tag/v0.1.0
