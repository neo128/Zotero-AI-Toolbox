# Contributing to PaperPilot

Thanks for your interest in improving PaperPilot.

## Quick Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp -n .env.example .env 2>/dev/null || true
```

## Before Opening a PR

1. Keep changes focused and small.
2. Update docs when behavior or CLI flags change.
3. Preserve backward compatibility for existing script flags when possible.
4. Run the basic smoke checks:

```bash
make ci
```

If `make` is not available in your environment, run:

```bash
python -m compileall scripts paperflow tests
python scripts/list_zotero_collections.py --help
python scripts/watch_and_import_papers.py --help
python scripts/langchain_pipeline.py --help
python -m unittest discover -s tests -p "test_*.py" -v
```

## Pull Request Guidelines

1. Use a clear title that describes user-facing impact.
2. Explain motivation, scope, and tradeoffs in the PR body.
3. Include before/after examples for CLI behavior when relevant.
4. If external APIs are involved, include a dry-run command in the PR description.

## Reporting Issues

- Use the Bug Report template for defects.
- Use the Feature Request template for improvements.
- Use the Usage Question template for setup/workflow help.
- Include exact command lines, logs, and environment details when possible.
- See `SUPPORT.md` for channel routing guidance.

## New Contributor Scope

- Start with `docs/GOOD_FIRST_ISSUES.md` for beginner-friendly tasks.
- Follow `docs/TRIAGE_POLICY.md` for SLA and lifecycle expectations.
