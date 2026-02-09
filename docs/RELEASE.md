# Release Guide

This guide keeps PaperPilot releases consistent and easy to consume.

## 1) Pre-release checklist

1. Ensure CI is green on `main`.
2. Run local verification:

```bash
make ci
```

3. Update curated notes in `CHANGELOG.md` under `[Unreleased]`.
4. Confirm migration notes for:
   - breaking CLI flag changes
   - new required environment variables
   - behavior changes in dedupe/import/sync scripts

## 2) Create a version tag

Use semantic versions:

- Patch: `v0.1.1`
- Minor: `v0.2.0`
- Major: `v1.0.0`

```bash
git checkout main
git pull
git tag v0.1.1
git push origin v0.1.1
```

Pushing the tag triggers `.github/workflows/release.yml` to publish the GitHub Release.

## 3) Draft release notes workflow

- `.github/workflows/release_drafter.yml` keeps a rolling draft release on `main`.
- `.github/release-drafter.yml` categorizes changes and appends migration hints.
- Before tagging, review and edit the draft release body if needed.

## 4) Post-release tasks

1. Move notable items from `[Unreleased]` to a version section in `CHANGELOG.md`.
2. Add compare links at the bottom of `CHANGELOG.md`.
3. Announce release highlights with:
   - key user-facing features/fixes
   - migration notes
   - one quickstart command that still works

## Migration Notes Template

```text
Breaking changes:
- None / <details>

Environment/config changes:
- None / Added <ENV_NAME>

Upgrade commands:
1) git pull
2) pip install -r requirements.txt
3) make ci
```
