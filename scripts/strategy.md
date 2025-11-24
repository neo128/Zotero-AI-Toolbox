# PaperPilot Script Strategies

This document summarizes the intent and core logic of the key scripts in the `scripts/` folder so that future contributors can quickly understand how each step works and how they fit together.

## watch_and_import_papers.py
- **Purpose**: Track trending papers (arXiv + HuggingFace) per `tag.json`, score them, dedupe against the existing Zotero library, and create new items.
- **Key Steps**:
  1. Load tag schema, HuggingFace trending lists (daily/weekly/monthly), and build a Zotero index for DOI/arXiv/URL/title-year.
  2. For each tag, fetch arXiv candidates within `--since-hours` and optionally inject HF trending matches.
  3. Enrich candidates with Semantic Scholar / CrossRef data, compute composite scores (recency + citations + HF weight), and select `--top-k`.
  4. Dedupe, optionally fill missing metadata (`--fill-missing`), create Zotero items/collections, and attach PDFs from arXiv/Unpaywall URLs.
  5. Write run logs + report JSON + `.data/new_items_watch.json` for downstream stages.

## fetch_missing_pdfs.py
- **Purpose**: Ensure newly added Zotero items have local PDF attachments.
- **Strategy**: Read `.data/new_items_watch.json` (fallback to dateAdded/Modified), inspect existing attachments, and download PDFs from best-effort sources (direct links, arXiv, Unpaywall, existing linked URLs). Save files under `auto_pdfs/<key>/` and create linked attachments.

## merge_zotero_duplicates.py
- **Purpose**: Merge duplicate bibliographic entries while preserving notes/attachments.
- **Strategy**: Group top-level items by DOI/URL/title-year, build `ItemBundle`s, pick winners based on PDF presence + recency, reparent children from losers, merge tags/collections, and delete duplicates (supports `--dry-run`).

## summarize_zotero_with_doubao.py
- **Purpose**: Generate AI summaries from local PDFs (Doubao/Qwen/openAI-compatible) and insert notes back into Zotero.
- **Strategy**: Iterate selected Zotero items (collection/tag/item-keys), locate PDF attachments within page/character limits, extract text via `pypdf`, call AI chat completions with configurable provider/model, render Markdown to HTML, and create notes (unless `--dry-run`). Optional local PDF mode writes summaries to files.

## enrich_zotero_abstracts.py
- **Purpose**: Fill `abstractNote` for items lacking abstracts.
- **Strategy**: Iterate collection/tag scope, skip notes/attachments, and attempt to fetch from URL meta tags → CrossRef (DOI) → Semantic Scholar (DOI/arXiv) → arXiv API. Update items via Zotero API with source tracking.

## sync_zotero_to_notion.py
- **Purpose**: Mirror Zotero items into a Notion database with optional AI enrichment.
- **Strategy**: Resolve collections/tags, build dynamic Notion property mapping from DB schema, generate Notion payloads (title/Authors/Year/Tags/URL/DOI/PDF link), optionally use AI extraction (Doubao/Qwen/OpenAI) to fill contributions/limitations/etc., and upsert Notion pages (dedupe by Zotero key/title).

## list_zotero_collections.py
- **Purpose**: Inspect Zotero collection hierarchy (for debugging and configuration).
- **Strategy**: Fetch all collections via Zotero API, print tree structure and optional item counts.

## import_ris_folder.py
- **Purpose**: Batch-import RIS files (from README exports, curated lists, etc.) into Zotero.
- **Strategy**: Walk a directory tree, parse RIS entries (title/URL/authors/year/tags), optionally ensure/create a target collection per file, dedupe by URL if requested, and POST batches to Zotero.

## import_embodied_ai_to_zotero.py & awesome_vla_to_ris.py
- **Purpose**: Parse curated GitHub README lists (Embodied AI / Awesome-VLA) and output RIS or direct Zotero entries.
- **Strategy**: Scrape README sections, collect metadata (title/URL/arXiv/DBLP), optionally enrich via arXiv/DBLP APIs, then either write `.ris` files or call Zotero API to create structured items/collections.

## delete_collection_notes.py
- **Purpose**: Cleanup notes under a specific collection (e.g., re-run summaries).
- **Strategy**: Resolve collection, iterate child items, and delete notes matching filters.

## ai_toolbox_pipeline.sh / langchain_pipeline.py
- **Purpose**: Orchestrate multi-stage flows (watch → PDF completion → dedupe → summaries → abstracts → Notion) via Bash or LangChain.
- **Strategy**: For Bash `--all` or per-stage flags trigger the corresponding scripts sequentially; for LangChain, compose `RunnableLambda`s, log stdout/stderr to timestamped files, and emit aggregate state JSON (including report/log paths).

## Supporting Files
- **ai_utils.py**: Resolve OpenAI-compatible provider config (Doubao/Qwen/custom), instantiate `OpenAI` clients for summarization/Notion enrichment.
- **utils_sources.py**: Shared helper functions for fetching arXiv/Semantic Scholar/CrossRef data, HuggingFace trending lists, HTML stripping, etc.
- **tag.json / tag_schema.json**: Define keywords/labels for auto-tagging & Notion mapping.

These strategies align with the README instructions and should help diagnose/extend individual stages quickly.
