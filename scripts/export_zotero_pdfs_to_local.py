#!/usr/bin/env python3
"""Mirror Zotero collections to local folders and copy PDF attachments."""
from __future__ import annotations

try:  # auto-load .env via sitecustomize if present
    import sitecustomize  # noqa: F401
except Exception:
    pass

import argparse
import os
import hashlib
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


PDF_MIME = "application/pdf"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPORT_DIR = ROOT / "exports" / "zotero_pdfs"


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


def sanitize_filename(name: str) -> str:
    cleaned = (name or "").strip() or "document"
    return re.sub(r"[\\/:*?\"<>|]", "_", cleaned)


def shorten_filename(name: str, max_len: int = 200) -> str:
    if len(name) <= max_len:
        return name
    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:10]
    keep = max_len - len(digest) - 1
    if keep < 1:
        return digest
    return f"{name[:keep]}_{digest}"


class ZoteroAPI:
    def __init__(
        self, user_id: str, api_key: str, timeout: int = 45, use_env_proxy: bool = True, retries: int = 3
    ) -> None:
        self.base = f"https://api.zotero.org/users/{user_id}"
        self.timeout = max(5, timeout)
        self.session = requests.Session()
        self.session.trust_env = use_env_proxy
        if not use_env_proxy:
            # Empty proxy dict disables proxies even if set globally.
            self.session.proxies = {}
        retry_cfg = Retry(
            total=max(0, retries),
            connect=max(0, retries),
            read=max(0, retries),
            status=max(0, retries),
            backoff_factor=1.0,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            raise_on_status=False,
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry_cfg)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update({"Zotero-API-Key": api_key, "User-Agent": "Zotero-Local-Export/0.1"})

    def fetch_collections(self) -> List[Dict[str, Optional[str]]]:
        url = f"{self.base}/collections"
        params = {"format": "json", "include": "data", "limit": 200}
        out: List[Dict[str, Optional[str]]] = []
        while url:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            for entry in resp.json():
                data = entry.get("data", {})
                out.append(
                    {
                        "key": entry.get("key"),
                        "name": data.get("name") or "(untitled)",
                        "parent": data.get("parentCollection") or None,
                    }
                )
            url = parse_next_link(resp.headers.get("Link"))
            params = None
        return out

    def iter_items(self, collection: Optional[str], limit: Optional[int]) -> Iterable[Dict[str, Any]]:
        url = f"{self.base}/items/top"
        if collection:
            url = f"{self.base}/collections/{collection}/items/top"
        params = {"format": "json", "include": "data", "limit": 100}
        remaining = limit if (limit and limit > 0) else None
        while url:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            payload = resp.json()
            for entry in payload:
                yield entry
                if remaining is not None:
                    remaining -= 1
                    if remaining == 0:
                        return
            url = parse_next_link(resp.headers.get("Link"))
            params = None

    def fetch_children(self, parent_key: str) -> List[Dict[str, Any]]:
        url = f"{self.base}/items/{parent_key}/children"
        params = {"format": "json", "include": "data", "limit": 100}
        out: List[Dict[str, Any]] = []
        while url:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            out.extend([entry.get("data", {}) for entry in resp.json()])
            url = parse_next_link(resp.headers.get("Link"))
            params = None
        return out


def iter_pdf_attachments(zot: ZoteroAPI, item_key: str) -> Iterable[Dict[str, Any]]:
    for child in zot.fetch_children(item_key):
        if child.get("itemType") != "attachment":
            continue
        filename = (child.get("filename") or "").lower()
        if child.get("contentType") == PDF_MIME or filename.endswith(".pdf"):
            yield child


def resolve_local_path(att: Dict[str, Any], storage_dir: Path) -> Optional[Path]:
    mode = (att.get("linkMode") or "").lower()
    if mode == "linked_file":
        raw = att.get("path")
        if not raw:
            return None
        if raw.startswith("storage:"):
            rel = raw.split("storage:", 1)[1].lstrip("/\\")
            return (storage_dir / rel).expanduser()
        return Path(raw).expanduser()
    if mode in {"imported_file", "imported_url"}:
        key = att.get("key")
        filename = att.get("filename")
        if key and filename:
            return storage_dir / key / filename
    return None


def ensure_pdf_local(att: Dict[str, Any], storage_dir: Path, temp_dir: Path) -> Optional[Path]:
    path = resolve_local_path(att, storage_dir)
    if path and path.exists():
        return path
    url = att.get("url") or att.get("path")
    if url and url.startswith("http"):
        try:
            resp = requests.get(url, timeout=45)
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - network error reporting
            print(f"[WARN] Failed to download {url}: {exc}")
            return None
        filename = sanitize_filename(att.get("filename") or att.get("title") or att.get("key") or "download")
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
        dest = temp_dir / filename
        dest.write_bytes(resp.content)
        return dest
    print(f"[WARN] Attachment {att.get('title') or att.get('key')} has no local file or downloadable URL")
    return None


def derive_pdf_filename(item: Dict[str, Any], att: Dict[str, Any]) -> str:
    title = item.get("title") or item.get("shortTitle") or att.get("title") or att.get("filename") or att.get("key")
    safe = sanitize_filename(title or "paper")
    if not safe.lower().endswith(".pdf"):
        safe += ".pdf"
    return shorten_filename(safe)


def build_collection_maps(collections: List[Dict[str, Optional[str]]]) -> Tuple[
    Dict[str, Dict[str, Optional[str]]], Dict[Optional[str], List[Dict[str, Optional[str]]]]
]:
    by_key: Dict[str, Dict[str, Optional[str]]] = {}
    children: Dict[Optional[str], List[Dict[str, Optional[str]]]] = {}
    for col in collections:
        by_key[col["key"]] = col
        parent = col.get("parent")
        children.setdefault(parent, []).append(col)
    return by_key, children


def resolve_collection_key(
    collections: Dict[str, Dict[str, Optional[str]]], name: Optional[str], key: Optional[str]
) -> Optional[str]:
    if key:
        return key
    if not name:
        return None
    for info in collections.values():
        if info.get("name") and info["name"].lower() == name.lower():
            return info["key"]
    raise SystemExit(f"Collection named '{name}' not found.")


def pick_attachment(attachments: List[Dict[str, Any]], storage_dir: Path) -> Optional[Dict[str, Any]]:
    for att in attachments:
        path = resolve_local_path(att, storage_dir)
        if path and path.exists():
            return att
    return attachments[0] if attachments else None


def ensure_dir(path: Path, dry_run: bool) -> None:
    if dry_run:
        return
    path.mkdir(parents=True, exist_ok=True)


def export_collection(
    zot: ZoteroAPI,
    collection: Dict[str, Optional[str]],
    children_map: Dict[Optional[str], List[Dict[str, Optional[str]]]],
    parent_dir: Path,
    storage_dir: Path,
    args: argparse.Namespace,
    temp_dir: Path,
) -> None:
    folder_name = sanitize_filename(collection.get("name") or collection["key"])
    target_dir = parent_dir / folder_name
    if args.dry_run:
        print(f"[DRY] Would ensure folder {target_dir}")
    else:
        ensure_dir(target_dir, dry_run=False)
    limit = args.limit if (args.limit and args.limit > 0) else None
    count = 0
    for entry in zot.iter_items(collection["key"], limit):
        data = entry.get("data", entry)
        item_key = data.get("key")
        title = data.get("title") or data.get("shortTitle") or "(untitled)"
        attachments = list(iter_pdf_attachments(zot, item_key)) if item_key else []
        if not attachments:
            continue
        filename = derive_pdf_filename(data, attachments[0])
        dest_path = target_dir / filename
        if dest_path.exists() and not args.overwrite:
            print(f"[SKIP] {title} already exists at {dest_path}")
            continue
        att = pick_attachment(attachments, storage_dir)
        if not att:
            continue
        local_path = ensure_pdf_local(att, storage_dir, temp_dir)
        if not local_path:
            continue
        if args.dry_run:
            print(f"[DRY] Would copy {local_path} → {dest_path}")
        else:
            ensure_dir(dest_path.parent, dry_run=False)
            shutil.copy2(local_path, dest_path)
            print(f"[OK] Saved {title} → {dest_path}")
        count += 1
    print(f"[COL] {collection.get('name')} exported PDFs: {count}")
    if args.recursive:
        for child in children_map.get(collection["key"], []):
            export_collection(zot, child, children_map, target_dir, storage_dir, args, temp_dir)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Export Zotero PDFs to local folders with collection hierarchy.")
    ap.add_argument("--collection", help="Zotero collection key to export (defaults to all top-level collections).")
    ap.add_argument("--collection-name", help="Zotero collection name to export.")
    ap.add_argument(
        "--output-dir",
        help="Base output directory (defaults to repo exports/zotero_pdfs or ZOTERO_PDF_EXPORT_DIR).",
    )
    ap.add_argument("--storage-dir", help="Override Zotero storage directory (defaults to ~/Zotero/storage).")
    ap.add_argument("--limit", type=int, default=0, help="Max items per collection (<=0 means no limit).")
    ap.add_argument("--no-recursive", dest="recursive", action="store_false", help="Do not descend into child collections.")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing files (default skips).")
    ap.add_argument("--dry-run", action="store_true", help="Preview folders/copies without writing files.")
    ap.add_argument("--zotero-timeout", type=int, default=45, help="HTTP timeout (seconds) for Zotero API.")
    ap.add_argument(
        "--zotero-retries",
        type=int,
        default=3,
        help="Retry count for Zotero API GET requests (handles transient SSL/connection errors).",
    )
    ap.add_argument(
        "--no-proxy",
        action="store_true",
        help="Ignore HTTP(S)_PROXY environment variables for Zotero API calls (useful if a local proxy breaks SSL).",
    )
    ap.set_defaults(recursive=True)
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    user_id = ensure_env("ZOTERO_USER_ID")
    api_key = ensure_env("ZOTERO_API_KEY")
    output_root = (
        Path(args.output_dir).expanduser()
        if args.output_dir
        else Path(os.environ.get("ZOTERO_PDF_EXPORT_DIR", DEFAULT_EXPORT_DIR)).expanduser()
    )
    storage_dir = Path(args.storage_dir or os.environ.get("ZOTERO_STORAGE_DIR", Path.home() / "Zotero" / "storage"))
    if not storage_dir.exists():
        print(f"[WARN] Zotero storage directory {storage_dir} does not exist; some attachments may fail.")
    if args.dry_run:
        print(f"[DRY] Output root: {output_root}")
    else:
        ensure_dir(output_root, dry_run=False)

    zot = ZoteroAPI(
        user_id,
        api_key,
        timeout=args.zotero_timeout,
        use_env_proxy=not args.no_proxy,
        retries=max(0, args.zotero_retries),
    )
    collections = zot.fetch_collections()
    by_key, children_map = build_collection_maps(collections)

    root_key = resolve_collection_key(by_key, args.collection_name, args.collection)
    if root_key:
        targets = [by_key[root_key]]
    else:
        targets = children_map.get(None, [])
        if not targets:
            raise SystemExit("No top-level collections found in Zotero library.")

    with tempfile.TemporaryDirectory(prefix="zotero_local_export_") as tmp_dir:
        temp_path = Path(tmp_dir)
        for col in targets:
            export_collection(zot, col, children_map, output_root, storage_dir, args, temp_path)


if __name__ == "__main__":
    main()
