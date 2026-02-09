# Before / After Examples

This page shows concrete improvements from real PaperPilot runs.

Data source:

- `logs/langchain_pipeline_20260120_163223.log`
- `logs/watch_20260120_163223.log`
- `reports/watch_20260120_163223.json`

## 1) Watch & Import

Before:

- Manual workflow usually requires searching multiple sources and importing entries one by one.
- Hard to keep consistent tags/collections.

After (single run, 24h window):

- `hf_candidates`: 124
- `added`: 17
- `skipped`: 19 duplicates
- `hf_overrides`: 20

Observed output snippet:

```text
[INFO] Done. Summary: {"candidates": 17, "added": 17, "skipped": 19, "updated": 0, "hf_candidates": 124, "hf_overrides": 20}
```

## 2) PDF Completion

Before:

- Newly imported items may miss local PDFs, blocking summary and downstream sync.

After:

- `PDFs added`: 17
- `remaining without PDF`: 1

Observed output snippet:

```text
[fetch-pdfs] [INFO] Completed. PDFs added: 17, remaining without PDF: 1.
```

## 3) Summarization Stage

Before:

- Reading and writing structured notes manually is time-consuming and inconsistent.

After:

- Stage auto-detected 52 recently modified items in scope.
- Notes created with repeated `[OK] Note created.` status for processed PDFs.

Observed output snippet:

```text
[summaries] [INFO] 52 items remain after applying modified-since 24.0h window.
[summaries]     [OK] Note created.
```

## 4) Dedupe Stage

Before:

- Duplicate checking in large libraries is error-prone and usually skipped.

After:

- Stage scans top-level items in the time window and reports deterministic status.

Observed output snippet:

```text
[dedupe] [INFO] Scanned 18 top-level items (after time filter).
[dedupe] [INFO] No duplicates detected with the current heuristic.
```
