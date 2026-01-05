#!/usr/bin/env python3
"""
Enrich missing Zotero metadata using URL / DOI / arXiv / PDF.
-------------------------------------------------------------

For each top-level Zotero item (optionally scoped by collection/tag),
try to fill missing fields such as title/date/DOI/abstract/authors using:
1) DOI detected in item fields or URL → CrossRef / Semantic Scholar
2) arXiv ID detected in URL → arXiv API
3) Optional PDF attachments/links → extract PDF metadata/text for DOI/title/year

Use --dry-run to preview updates.
"""
from __future__ import annotations

try:  # auto-load .env via sitecustomize if present
    import sitecustomize  # noqa: F401
except Exception:
    pass

import argparse
import datetime as dt
import io
import os
import re
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
import xml.etree.ElementTree as ET

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - optional dependency
    PdfReader = None

from utils_sources import (
    ATOM_NS,
    ARXIV_NS,
    fetch_crossref_metadata,
    fetch_s2_metadata,
    normalize_authors,
    parse_arxiv_doi,
    parse_arxiv_pdf,
    parse_authors,
    strip_tags,
)

DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'>]+", re.I)
ARXIV_URL_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/([A-Za-z0-9.\-]+)", re.I)


def ensure_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def parse_next_link(link_header: Optional[str]) -> Optional[str]:
    if not link_header:
        return None
    for chunk in link_header.split(","):
        parts = chunk.split(";")
        if len(parts) < 2:
            continue
        url_part = parts[0].strip()
        rel_part = parts[1].strip()
        if rel_part == 'rel="next"':
            return url_part.strip("<>")
    return None


def parse_iso8601(value: Optional[str]) -> Optional[dt.datetime]:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return dt.datetime.fromisoformat(value)
    except Exception:
        return None


def clean_doi(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    doi = raw.strip()
    doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
    doi = doi.replace("doi:", "").strip()
    return doi or None


def extract_doi_from_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    m = DOI_RE.search(url)
    if m:
        candidate = m.group(0).rstrip(").,;")
        return clean_doi(candidate)
    return None


def extract_arxiv_id(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    m = ARXIV_URL_RE.search(url)
    if m:
        return m.group(1)
    return None


def fetch_arxiv_metadata(arxiv_id: str) -> Dict[str, Any]:
    url = "http://export.arxiv.org/api/query"
    try:
        resp = requests.get(url, params={"id_list": arxiv_id}, timeout=20, headers={"User-Agent": "Zotero-Meta/0.1"})
        resp.raise_for_status()
    except Exception:
        return {}
    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError:
        return {}
    entry = root.find(f"{ATOM_NS}entry")
    if entry is None:
        return {}
    title = (entry.findtext(f"{ATOM_NS}title") or "").strip()
    summary = strip_tags(entry.findtext(f"{ATOM_NS}summary") or "")
    published = entry.findtext(f"{ATOM_NS}published") or entry.findtext(f"{ATOM_NS}updated")
    date_str = published.split("T")[0] if published else None
    year = published[:4] if published else None
    authors = parse_authors(entry)
    pdf_url = parse_arxiv_pdf(entry)
    doi = parse_arxiv_doi(entry)
    abs_url = f"https://arxiv.org/abs/{arxiv_id}"
    return {
        "title": title,
        "abstract": summary,
        "authors": authors,
        "date": date_str,
        "year": year,
        "url": abs_url,
        "pdf_url": pdf_url,
        "doi": doi,
    }


def fetch_pdf_bytes_via_api(session: requests.Session, base: str, key: str, max_bytes: int) -> Optional[bytes]:
    url = f"{base}/items/{key}/file"
    try:
        resp = session.get(url, stream=True, timeout=60)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        buf = io.BytesIO()
        size = 0
        for chunk in resp.iter_content(chunk_size=8192):
            if not chunk:
                continue
            size += len(chunk)
            if size > max_bytes:
                return None
            buf.write(chunk)
        return buf.getvalue()
    except Exception:
        return None


def fetch_pdf_bytes_from_url(url: str, max_bytes: int) -> Optional[bytes]:
    try:
        resp = requests.get(url, stream=True, timeout=40)
        resp.raise_for_status()
        buf = io.BytesIO()
        size = 0
        for chunk in resp.iter_content(chunk_size=8192):
            if not chunk:
                continue
            size += len(chunk)
            if size > max_bytes:
                return None
            buf.write(chunk)
        return buf.getvalue()
    except Exception:
        return None


def extract_pdf_metadata(content: bytes) -> Dict[str, Any]:
    if not PdfReader:
        return {}
    try:
        reader = PdfReader(io.BytesIO(content))
    except Exception:
        return {}
    meta: Dict[str, Any] = {}
    doc_info = getattr(reader, "metadata", None)
    if doc_info:
        title = getattr(doc_info, "title", None) or doc_info.get("/Title")
        if title:
            meta["title"] = title.strip()
        author = getattr(doc_info, "author", None) or doc_info.get("/Author")
        if author:
            meta["authors"] = [author]
    try:
        first_page = reader.pages[0] if reader.pages else None
    except Exception:
        first_page = None
    text = ""
    if first_page:
        try:
            text = first_page.extract_text() or ""
        except Exception:
            text = ""
    if text:
        doi = extract_doi_from_url(text)
        if doi:
            meta["doi"] = doi
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        for ln in lines:
            if "abstract" in ln.lower():
                break
            if 10 < len(ln) <= 200 and len(ln.split()) >= 4:
                if "title" not in meta:
                    meta["title"] = ln
                break
        year_match = re.search(r"\b(19|20)\d{2}\b", text)
        if year_match and "year" not in meta:
            meta["year"] = year_match.group(0)
    return meta


def merge_meta(target: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    for key, val in incoming.items():
        if val is None:
            continue
        if key not in target or not target[key]:
            target[key] = val
    return target


def map_item_type(meta: Dict[str, Any], current: Optional[str]) -> Optional[str]:
    if current and current not in {"webpage", "document", "report"}:
        return None
    cr_type = meta.get("type")
    types = meta.get("types") or []
    if isinstance(types, str):
        types = [types]
    candidates = [cr_type] + list(types)
    for t in candidates:
        if not t:
            continue
        t = t.lower()
        if t in {"journal-article", "article", "review-article"}:
            return "journalArticle"
        if t in {"proceedings-article", "conference-paper", "conference"}:
            return "conferencePaper"
        if t in {"book-chapter", "book-section"}:
            return "bookSection"
        if t in {"book"}:
            return "book"
        if t in {"dataset"}:
            return "dataset"
        if t in {"report"}:
            return "report"
    if meta.get("container"):
        return "journalArticle"
    return None


def build_updates(data: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
    updates: Dict[str, Any] = {}

    def maybe_set(field: str, value: Any) -> None:
        if value is None:
            return
        current = data.get(field)
        if current:
            if isinstance(current, list) and len(current) == 0:
                updates[field] = value
            return
        updates[field] = value

    maybe_set("title", meta.get("title"))
    date_val = meta.get("date") or (meta.get("year") and str(meta.get("year")))
    maybe_set("date", date_val)
    maybe_set("DOI", meta.get("doi"))
    maybe_set("url", meta.get("url"))
    maybe_set("abstractNote", meta.get("abstract"))
    authors = meta.get("authors")
    if authors and not data.get("creators"):
        updates["creators"] = normalize_authors(authors)
    item_type = map_item_type(meta, data.get("itemType"))
    if item_type:
        updates["itemType"] = item_type
    # Publication fields
    container = meta.get("container")
    if item_type == "journalArticle":
        maybe_set("publicationTitle", container)
        maybe_set("volume", meta.get("volume"))
        maybe_set("issue", meta.get("issue"))
        maybe_set("pages", meta.get("pages"))
        maybe_set("publisher", meta.get("publisher"))
    elif item_type == "conferencePaper":
        maybe_set("conferenceName", meta.get("venue") or container)
        maybe_set("proceedingsTitle", container)
        maybe_set("publisher", meta.get("publisher"))
        maybe_set("pages", meta.get("pages"))
    return updates
    return updates


def needs_enrichment(data: Dict[str, Any]) -> bool:
    if data.get("itemType") in {"note", "attachment"}:
        return False
    if not data.get("title"):
        return True
    if not data.get("date") and not data.get("year"):
        return True
    if not data.get("DOI"):
        return True
    if not data.get("abstractNote"):
        return True
    if not data.get("creators"):
        return True
    if (data.get("itemType") in {"webpage", "document"} or not data.get("itemType")) and not data.get(
        "publicationTitle"
    ):
        return True
    return False


class ZoteroAPI:
    def __init__(self, user_id: str, api_key: str) -> None:
        self.base = f"https://api.zotero.org/users/{user_id}"
        self.session = requests.Session()
        self.session.headers.update({"Zotero-API-Key": api_key, "User-Agent": "Zotero-Meta-Enricher/0.1"})

    def list_collections(self) -> Dict[str, Dict[str, Optional[str]]]:
        resp = self.session.get(f"{self.base}/collections", params={"limit": 200, "format": "json", "include": "data"})
        resp.raise_for_status()
        out: Dict[str, Dict[str, Optional[str]]] = {}
        for entry in resp.json():
            data = entry.get("data", {})
            out[data.get("name")] = {"key": entry.get("key"), "parent": data.get("parentCollection")}
        return out

    def iter_top_items(
        self,
        collection: Optional[str],
        tag: Optional[str],
        limit: Optional[int],
    ) -> Iterable[Dict[str, Any]]:
        if collection:
            url = f"{self.base}/collections/{collection}/items/top"
        else:
            url = f"{self.base}/items/top"
        params = {"format": "json", "include": "data", "limit": 100}
        if tag:
            params["tag"] = tag
        remaining = limit if limit and limit > 0 else None
        while url:
            resp = self.session.get(url, params=params)
            resp.raise_for_status()
            for entry in resp.json():
                yield {"key": entry["key"], "version": entry["version"], "data": entry["data"]}
                if remaining is not None:
                    remaining -= 1
                    if remaining == 0:
                        return
            url = parse_next_link(resp.headers.get("Link"))
            params = None

    def fetch_children(self, parent_key: str) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        url = f"{self.base}/items/{parent_key}/children"
        params = {"format": "json", "include": "data", "limit": 100}
        while url:
            resp = self.session.get(url, params=params)
            resp.raise_for_status()
            for entry in resp.json():
                results.append({"key": entry["key"], "version": entry["version"], "data": entry["data"]})
            url = parse_next_link(resp.headers.get("Link"))
            params = None
        return results

    def update_item(self, entry: Dict[str, Any], new_data: Dict[str, Any]) -> None:
        headers = {"If-Unmodified-Since-Version": str(entry["version"])}
        resp = self.session.put(f"{self.base}/items/{entry['key']}", json=new_data, headers=headers)
        if resp.status_code >= 400:
            body = resp.text
            print(f"[ERROR] Update failed {resp.status_code} for {entry['key']}: {body[:300]}")
        resp.raise_for_status()


def resolve_collection_key(api: ZoteroAPI, args: argparse.Namespace) -> Optional[str]:
    if args.collection:
        return args.collection
    if not args.collection_name:
        return None
    collections = api.list_collections()
    for name, info in collections.items():
        if not name:
            continue
        if name == args.collection_name or name.lower() == args.collection_name.lower():
            print(f"[INFO] Resolved collection '{name}' → {info['key']}")
            return info["key"]
    raise SystemExit(f"Collection named '{args.collection_name}' not found.")


def collect_pdf_sources(data: Dict[str, Any], children: List[Dict[str, Any]]) -> List[Tuple[str, str]]:
    sources: List[Tuple[str, str]] = []
    url = data.get("url") or ""
    if url.lower().endswith(".pdf"):
        sources.append(("url", url))
    for child in children:
        cdata = child["data"]
        if cdata.get("itemType") != "attachment":
            continue
        if cdata.get("contentType") != "application/pdf":
            continue
        link_mode = cdata.get("linkMode") or ""
        child_url = cdata.get("url") or ""
        if link_mode == "linked_url" and child_url:
            sources.append(("url", child_url))
        else:
            sources.append(("api", child["key"]))
    return sources


def collect_metadata_for_item(
    api: ZoteroAPI,
    entry: Dict[str, Any],
    children: List[Dict[str, Any]],
    use_pdf: bool,
    max_pdf_bytes: int,
) -> Tuple[Dict[str, Any], List[str]]:
    data = entry["data"]
    meta: Dict[str, Any] = {}
    sources: List[str] = []

    doi_candidates: List[str] = []
    if data.get("DOI"):
        candidate = clean_doi(data.get("DOI"))
        if candidate:
            doi_candidates.append(candidate)
    doi_from_url = extract_doi_from_url(data.get("url"))
    if doi_from_url:
        doi_candidates.append(doi_from_url)

    arxiv_id = extract_arxiv_id(data.get("url"))

    if arxiv_id:
        arxiv_meta = fetch_arxiv_metadata(arxiv_id)
        if arxiv_meta:
            meta = merge_meta(meta, arxiv_meta)
            sources.append("arXiv")
        if arxiv_meta.get("doi"):
            doi_candidates.append(clean_doi(arxiv_meta["doi"]))

    for doi in doi_candidates:
        if not doi:
            continue
        cr = fetch_crossref_metadata(doi)
        if cr:
            meta = merge_meta(meta, {**cr, "doi": doi})
            sources.append("CrossRef")
        s2 = fetch_s2_metadata("DOI", doi)
        if s2:
            meta = merge_meta(meta, {"title": s2.get("title"), "abstract": s2.get("abstract"), "year": s2.get("year")})
            if s2.get("doi"):
                meta = merge_meta(meta, {"doi": s2["doi"]})
            if s2.get("citationCount") is not None and "extra" not in meta:
                meta["extra"] = f"Citations: {s2['citationCount']}"
            sources.append("SemanticScholar")

    if use_pdf:
        pdf_sources = collect_pdf_sources(data, children)
        for source_type, ref in pdf_sources:
            content: Optional[bytes]
            if source_type == "url":
                content = fetch_pdf_bytes_from_url(ref, max_pdf_bytes)
            else:
                content = fetch_pdf_bytes_via_api(api.session, api.base, ref, max_pdf_bytes)
            if not content:
                continue
            pdf_meta = extract_pdf_metadata(content)
            if pdf_meta:
                meta = merge_meta(meta, pdf_meta)
                sources.append("PDF")
                if pdf_meta.get("doi"):
                    doi = clean_doi(pdf_meta["doi"])
                    if doi and doi not in doi_candidates:
                        # enrich using DOI found in PDF if we still lack details
                        cr = fetch_crossref_metadata(doi)
                        if cr:
                            meta = merge_meta(meta, {**cr, "doi": doi})
                            sources.append("CrossRef")
                        s2 = fetch_s2_metadata("DOI", doi)
                        if s2:
                            meta = merge_meta(
                                meta, {"title": s2.get("title"), "abstract": s2.get("abstract"), "year": s2.get("year")}
                            )
                            if s2.get("doi"):
                                meta = merge_meta(meta, {"doi": s2["doi"]})
                            sources.append("SemanticScholar")
    return meta, sources


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Fill missing Zotero metadata via URL/DOI/arXiv/PDF.")
    ap.add_argument("--collection", help="Collection key to scope items.")
    ap.add_argument("--collection-name", help="Collection name to scope items.")
    ap.add_argument("--tag", help="Only process items containing this tag.")
    ap.add_argument("--limit", type=int, default=0, help="Max number of items to scan (<=0 means no limit).")
    ap.add_argument(
        "--modified-since-hours",
        type=float,
        default=0.0,
        help="Only process items modified within the last N hours (<=0 disables).",
    )
    ap.add_argument("--use-pdf", action="store_true", help="Also inspect PDF attachments/links for DOI/title/year.")
    ap.add_argument("--max-pdf-bytes", type=int, default=8_000_000, help="Skip PDFs larger than this many bytes.")
    ap.add_argument("--dry-run", action="store_true", help="Preview updates without writing to Zotero.")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    user_id = ensure_env("ZOTERO_USER_ID")
    api_key = ensure_env("ZOTERO_API_KEY")
    api = ZoteroAPI(user_id, api_key)

    if args.use_pdf and not PdfReader:
        print("[WARN] pypdf is not installed; PDF-based enrichment will be skipped.")

    collection_key = resolve_collection_key(api, args)
    limit = args.limit if args.limit > 0 else None

    items = list(api.iter_top_items(collection_key, args.tag, limit))
    if args.modified_since_hours and args.modified_since_hours > 0:
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=args.modified_since_hours)
        filtered: List[Dict[str, Any]] = []
        for entry in items:
            dm = parse_iso8601(entry["data"].get("dateModified"))
            if dm and dm < cutoff:
                continue
            filtered.append(entry)
        items = filtered

    print(f"[INFO] Loaded {len(items)} top-level items.")

    updated = 0
    scanned = 0
    for entry in items:
        data = entry["data"]
        if data.get("itemType") in {"note", "attachment"}:
            continue
        if not needs_enrichment(data):
            continue
        scanned += 1
        children = api.fetch_children(entry["key"])
        meta, sources = collect_metadata_for_item(api, entry, children, args.use_pdf, args.max_pdf_bytes)
        updates = build_updates(data, meta)
        if not updates:
            continue
        new_data = data.copy()
        new_data.update(updates)
        if args.dry_run:
            print(f"[DRY] Would update {entry['key']} ({data.get('title') or 'untitled'}) via {sources}: {updates}")
        else:
            try:
                api.update_item(entry, new_data)
            except requests.HTTPError:
                continue
            updated += 1
            print(f"[OK] Updated {entry['key']} ({data.get('title') or 'untitled'}) via {sources}: {list(updates)}")

    print(f"[INFO] Done. Candidates scanned: {scanned}, items updated: {updated}.")


if __name__ == "__main__":
    main()
