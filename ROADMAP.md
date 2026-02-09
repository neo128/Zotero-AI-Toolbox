# Roadmap

This roadmap highlights near-term priorities to improve PaperPilot's reliability, usability, and community adoption.

## Milestone 1: Foundation (Done)

- [x] License and governance files
- [x] CI smoke checks for core CLI scripts
- [x] Issue/PR templates and release workflow
- [x] Changelog baseline and dual-language README improvements

## Milestone 2: Developer Experience (In Progress)

- [x] Add local `Makefile` commands (`install`, `check`, `test`, `ci`)
- [x] Add minimal unit tests for CLI availability
- [x] Add sample `.env` presets for common paths:
  - Zotero-only
  - Zotero + Notion
- [x] Add a compact troubleshooting matrix by error pattern

## Milestone 3: Showcase and Growth (Done)

- [x] Add before/after examples for:
  - watch-import
  - dedupe
  - summarize
- [x] Publish regular release notes (`v0.x.y`) with migration hints

## Milestone 4: Reliability and Coverage (Planned)

- [x] Add unit tests for argument parsing and scoring logic
- [x] Add fixture-based tests for dedupe and metadata enrichment
- [x] Add smoke checks for docs command snippets
- [x] Add dependency update automation

## Success Metrics

- Weekly repository activity with at least one meaningful update
- Consistent passing CI on pull requests
- Lower issue turnaround time through reproducible templates
- Higher newcomer completion rate for first-run setup
