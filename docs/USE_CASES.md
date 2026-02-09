# Use Cases

This document provides practical starting points for common PaperPilot workflows.

## 1) Daily Paper Watch (Zotero-only)

Goal: Keep a focused collection updated with recent papers.

```bash
python scripts/watch_and_import_papers.py \
  --tags ./tag.json \
  --since-hours 24 \
  --top-k 10 \
  --min-score 0.3 \
  --create-collections
```

Then attach missing PDFs:

```bash
python scripts/fetch_missing_pdfs.py --since-hours 24 --new-items-json .data/new_items_watch.json
```

## 2) Library Cleanup + AI Notes

Goal: Keep a large Zotero library searchable and review-ready.

```bash
python scripts/merge_zotero_duplicates.py --dry-run
python scripts/merge_zotero_duplicates.py --collection-name "Embodied AI" --limit 200
python scripts/summarize_zotero_with_doubao.py --limit 50 --insert-note --summary-dir ./summaries
```

## 3) End-to-End Pipeline (Zotero + Notion)

Goal: Run collection maintenance and sync to Notion as one flow.

```bash
python scripts/langchain_pipeline.py \
  --collection-name "Embodied AI" \
  --watch-since-hours 24 \
  --summary-limit 150 \
  --abstract-limit 400 \
  --notion-limit 500
```

Preview only:

```bash
scripts/ai_toolbox_pipeline.sh --watch-import --notion-sync --dry-run
```
