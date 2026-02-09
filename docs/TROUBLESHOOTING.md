# Troubleshooting

This matrix maps common failure patterns to fast checks and fixes.

## 1) Auth / Permission Errors

Symptoms:

- `401 Unauthorized`
- `403 Forbidden`
- Notion/Zotero API requests fail immediately

Checks:

- Verify `.env` exists and values are non-empty.
- Confirm `ZOTERO_USER_ID` and `ZOTERO_API_KEY` are from the same account.
- Confirm `NOTION_TOKEN` has access to the target database.

Fixes:

- Re-generate API keys and retry.
- Re-share Notion database with the integration and re-copy `NOTION_DATABASE_ID`.

## 2) "No matching items" / Empty Results

Symptoms:

- Script runs but reports zero candidates/items.

Checks:

- Collection names and tags are exact matches.
- Time window filters are not too strict (`--since-hours`, `--since-days`).
- `--limit` is not too low.

Fixes:

- Start with broader scope:
  - increase `--since-hours`
  - remove restrictive tag/collection filters
- Run collection introspection:

```bash
python scripts/list_zotero_collections.py --items 0
```

## 3) PDF Not Found / Cannot Summarize

Symptoms:

- Summarizer skips items due to missing local PDF.

Checks:

- Attachments are local files or valid linked files.
- `ZOTERO_STORAGE_DIR` points to your actual Zotero storage path.

Fixes:

```bash
python scripts/fetch_missing_pdfs.py --since-hours 24 --new-items-json .data/new_items_watch.json
```

## 4) AI Provider 400/429/Timeout

Symptoms:

- `400 Bad Request`, `429 Too Many Requests`, or request timeout from AI endpoint.

Checks:

- Correct provider/model/api key combination.
- API base URL and endpoint compatibility.
- Request size (too many pages/chars).

Fixes:

- Reduce input size: `--max-pages`, `--max-chars`.
- Lower throughput / retry later if rate-limited.
- Validate provider config in `.env`.

## 5) Notion Mapping Errors

Symptoms:

- Sync fails or some fields are skipped.

Checks:

- Database property names align with script expectations.
- Property types are compatible (text/select/multi-select/url).

Fixes:

- Start with dry-run:

```bash
python scripts/sync_zotero_to_notion.py --dry-run --limit 20
```

- Align database schema and retry.

## 6) Quick Recovery Command

When unsure, run a safe baseline:

```bash
make ci
python scripts/langchain_pipeline.py --help
```
